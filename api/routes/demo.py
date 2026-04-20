"""Demo UI + endpoints using the full agent/node pipeline."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from app.agents.coordinator_agent import CoordinatorAgent
from app.agents.processor_agent import ProcessorAgent
from app.agents.validator_agent import ValidatorAgent
from app.database.models import ScheduledPost, SessionLocal
from app.graphs.multi_agent_graph import route_after_validator
from app.nodes.fetch_trends_node import FetchTrendsNode
from app.nodes.generate_posts_node import generate_posts
from app.nodes.publish_post_node import publish_post
from app.services.scheduler import schedule_post

router = APIRouter(prefix="/demo", tags=["demo"])


class DemoGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=500)
    region: str = Field(default="united_states", min_length=2, max_length=64)


class DemoPublishRequest(BaseModel):
    variant: Literal["thought_leadership", "question_hook", "data_insight"]
    generated_posts: dict[str, Any]
    edited_text: str | None = None
    scheduled_time: str | None = None  # ISO 8601 datetime string for scheduling


@router.post("/generate")
async def demo_generate(body: DemoGenerateRequest):
    """Run core generation flow via agents/nodes and return 3 variants."""
    prompt = body.prompt.strip()
    region = body.region.strip() or "united_states"
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required.")

    coordinator = CoordinatorAgent()
    processor = ProcessorAgent()
    fetch_trends = FetchTrendsNode(processor)

    state: dict[str, Any] = {
        "input": prompt,
        "region": region,
        "execution_history": [],
        "retry_count": 0,
        "max_retries": 3,
    }

    try:
        state = coordinator.execute(state)
        next_agent = state.get("next_agent", "processor")

        if next_agent == "fetch_trends":
            state = fetch_trends(state)
            trends_status = str((state.get("trends_metadata") or {}).get("status") or "completed")
            trends_preview_raw = state.get("trends") or []
            trends_preview = trends_preview_raw[:5] if isinstance(trends_preview_raw, list) else []
        else:
            state = processor.execute(state)
            trends_status = "skipped"
            trends_preview = []

        state = generate_posts(state)
        generated_posts = state.get("generated_posts") or {}
        if not generated_posts:
            raise RuntimeError(state.get("generate_posts_error") or "No generated posts")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}") from e

    return {
        "ok": True,
        "steps": {
            "trends": trends_status,
            "generation": "completed",
            "approval": "pending",
            "publish": "pending",
        },
        "topic_used": prompt,
        "trends_preview": trends_preview,
        "generation_context": state.get("generate_posts_context"),
        "generated_posts": generated_posts,
        "execution_history": state.get("execution_history", []),
    }


@router.post("/publish")
async def demo_publish(body: DemoPublishRequest):
    """Run approval->validator->publish_post pipeline. Supports immediate or scheduled publishing."""
    try:
        generated_posts = body.generated_posts or {}
        selected = generated_posts.get(body.variant) if isinstance(generated_posts, dict) else None
        if not isinstance(selected, dict):
            raise RuntimeError("Selected variant is missing from generated_posts.")

        edited = (body.edited_text or "").strip()
        if edited:
            approved_text = edited
        else:
            body_txt = str(selected.get("body") or "").strip()
            hashtags = selected.get("hashtags") or []
            tags = " ".join(
                f"#{str(h).lstrip('#').strip()}" for h in hashtags if str(h).strip()
            )
            approved_text = f"{body_txt}\n\n{tags}".strip()

        # If scheduled_time is provided, schedule the post instead of publishing immediately
        if body.scheduled_time:
            try:
                scheduled_dt = datetime.fromisoformat(body.scheduled_time.replace("Z", "+00:00"))
                if scheduled_dt.tzinfo is None:
                    scheduled_dt = scheduled_dt.replace(tzinfo=timezone.utc)
                else:
                    scheduled_dt = scheduled_dt.astimezone(timezone.utc)
                
                if scheduled_dt <= datetime.now(timezone.utc):
                    raise ValueError("Scheduled time must be in the future")
                
                # Create scheduled post in database
                db = SessionLocal()
                try:
                    post = ScheduledPost(
                        variant=body.variant,
                        content=approved_text,
                        hashtags=json.dumps(selected.get("hashtags", [])),
                        scheduled_time=scheduled_dt,
                        status="pending",
                    )
                    db.add(post)
                    db.commit()
                    db.refresh(post)
                    
                    # Schedule with APScheduler
                    job_id = schedule_post(post.id, scheduled_dt)
                    
                    return {
                        "ok": True,
                        "scheduled": True,
                        "post_id": post.id,
                        "scheduled_time": scheduled_dt.isoformat(),
                        "used_variant": body.variant,
                        "message": f"Post scheduled for {scheduled_dt.isoformat()} (job: {job_id})",
                    }
                finally:
                    db.close()
                    
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

        # Immediate publishing (original flow)
        state: dict[str, Any] = {
            "execution_history": [],
            "approved_for_publish": True,
            "approved_content": approved_text,
            "publish_draft_text": approved_text,
            "selected_variant": body.variant,
            # Validator expects processed output fields.
            "processed_output": {"result": approved_text, "metadata": {"status": "success"}},
            "processor_confidence": 1.0,
            "retry_count": 0,
            "max_retries": 3,
        }

        validator = ValidatorAgent()
        state = validator.execute(state)
        route = route_after_validator(state)
        if route != "publish_post":
            return {
                "ok": False,
                "used_variant": body.variant,
                "steps": {"approval": "completed", "validator": state.get("validator_status"), "publish": "skipped"},
                "detail": "Validation did not route to publish_post.",
                "state": {
                    "is_valid": state.get("is_valid"),
                    "validation_score": state.get("validation_score"),
                },
            }

        state = publish_post(state)
        if state.get("publish_post_status") != "completed":
            raise RuntimeError(str(state.get("publish_post_error") or "Publish failed."))

        return {
            "ok": True,
            "scheduled": False,
            "used_variant": body.variant,
            "steps": {"approval": "completed", "validator": "completed", "publish": "completed"},
            "linkedin": {"id": state.get("linkedin_post_urn")},
            "execution_history": state.get("execution_history", []),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("", response_class=HTMLResponse)
async def demo_page():
    """Single-page demo UI (no extra frontend dependencies)."""
    return HTMLResponse(
        """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Trend2Post Studio</title>
  <style>
    body { font-family: Inter, Arial, sans-serif; margin: 0; background: #0b1020; color: #e9eefb; }
    .wrap { max-width: 1080px; margin: 24px auto; padding: 0 16px; }
    .card { background: #131a2e; border: 1px solid #243255; border-radius: 12px; padding: 14px; margin-bottom: 14px; }
    h1 { margin: 0 0 12px 0; font-size: 24px; }
    input, textarea, button { font: inherit; border-radius: 10px; border: 1px solid #2d3f6b; }
    input, textarea { width: 100%; padding: 10px; background: #0e1630; color: #e9eefb; }
    textarea { min-height: 140px; resize: vertical; }
    button { padding: 10px 14px; background: #3f74ff; color: #fff; cursor: pointer; border: none; }
    button:disabled { opacity: .6; cursor: not-allowed; }
    .row { display: grid; grid-template-columns: 1fr 180px; gap: 10px; }
    .chips { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px; }
    .chip { padding: 4px 8px; border-radius: 999px; border: 1px solid #35508d; color: #b7c6f5; font-size: 12px; }
    .grid3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
    .variant { border: 1px solid #2a3a63; border-radius: 10px; padding: 10px; background: #10172a; }
    .variant.active { border-color: #79a2ff; box-shadow: 0 0 0 1px #79a2ff inset; }
    .small { color: #9bb0e9; font-size: 13px; }
    .ok { color: #77e3a6; }
    .err { color: #ff8fa3; white-space: pre-wrap; }
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Trend2Post Studio</h1>

    <div class="card">
      <div class="row">
        <input id="prompt" placeholder="Enter prompt (e.g. AI trends in marketing this week)" />
        <button id="generateBtn">Generate 3 Variants</button>
      </div>
      <div class="chips" id="steps"></div>
      <div class="small" id="topicUsed"></div>
    </div>

    <div class="card">
      <div class="grid3" id="variants"></div>
    </div>

    <div class="card">
      <div class="small">Selected variant (editable before publish)</div>
      <textarea id="editor" placeholder="Variant content appears here..."></textarea>
      <div style="margin-top:10px; display:flex; gap:10px;">
        <button id="publishBtn" disabled>Approve & Publish to LinkedIn</button>
      </div>
      <div style="margin-top:10px;" id="result"></div>
    </div>
  </div>

  <script>
    const stepsEl = document.getElementById('steps');
    const variantsEl = document.getElementById('variants');
    const editor = document.getElementById('editor');
    const resultEl = document.getElementById('result');
    const topicUsedEl = document.getElementById('topicUsed');
    const generateBtn = document.getElementById('generateBtn');
    const publishBtn = document.getElementById('publishBtn');

    let generatedPosts = null;
    let selectedVariant = null;

    function renderSteps(steps) {
      stepsEl.innerHTML = '';
      Object.entries(steps).forEach(([k, v]) => {
        const div = document.createElement('div');
        div.className = 'chip';
        div.textContent = `${k}: ${v}`;
        stepsEl.appendChild(div);
      });
    }

    function toVariantText(v) {
      const body = (v.body || '').trim();
      const tags = (v.hashtags || []).map(h => `#${String(h).replace(/^#/, '')}`).join(' ');
      return `${body}\\n\\n${tags}`.trim();
    }

    function renderVariants(data) {
      variantsEl.innerHTML = '';
      const keys = ['thought_leadership', 'question_hook', 'data_insight'];
      keys.forEach((k) => {
        const v = data[k];
        const card = document.createElement('div');
        card.className = 'variant';
        card.innerHTML = `<b>${k}</b><div class="small" style="margin:8px 0;">${(v.body || '').slice(0, 220)}</div><div class="small">${(v.hashtags || []).map(h => '#' + h).join(' ')}</div>`;
        card.onclick = () => {
          document.querySelectorAll('.variant').forEach(x => x.classList.remove('active'));
          card.classList.add('active');
          selectedVariant = k;
          editor.value = toVariantText(v);
          publishBtn.disabled = false;
        };
        variantsEl.appendChild(card);
      });
    }

    generateBtn.onclick = async () => {
      resultEl.innerHTML = '';
      publishBtn.disabled = true;
      selectedVariant = null;
      generatedPosts = null;
      const prompt = document.getElementById('prompt').value.trim();
      if (!prompt) return;
      generateBtn.disabled = true;
      try {
        const res = await fetch('/demo/generate', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ prompt, region: 'united_states' })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Generation failed');
        generatedPosts = data.generated_posts;
        renderSteps(data.steps || {});
        topicUsedEl.textContent = data.topic_used ? `Topic used: ${data.topic_used}` : '';
        renderVariants(generatedPosts);
      } catch (e) {
        resultEl.innerHTML = `<div class="err">${e.message}</div>`;
      } finally {
        generateBtn.disabled = false;
      }
    };

    publishBtn.onclick = async () => {
      if (!generatedPosts || !selectedVariant) return;
      publishBtn.disabled = true;
      resultEl.innerHTML = '';
      try {
        const res = await fetch('/demo/publish', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            variant: selectedVariant,
            generated_posts: generatedPosts,
            edited_text: editor.value.trim()
          })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Publish failed');
        const urn = (data.linkedin && data.linkedin.id) || '';
        resultEl.innerHTML = `<div class="ok">Published successfully. ${urn ? `URN: <code>${urn}</code>` : ''}</div>`;
      } catch (e) {
        resultEl.innerHTML = `<div class="err">${e.message}</div>`;
      } finally {
        publishBtn.disabled = false;
      }
    };
  </script>
</body>
</html>
        """
    )