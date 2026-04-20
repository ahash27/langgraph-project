"""Human approval node - pauses execution for human review using LangGraph interrupt."""

from typing import Dict, Union
from langgraph.types import interrupt, Command
from app.graphs.state_schema import AgentState, JSONValue
from app.utils.logger import log_agent_step


class HumanApprovalNode:
    """
    Human approval node that pauses workflow execution for human review.
    
    This node uses LangGraph's interrupt/resume mechanism to:
    - Pause execution and request human approval
    - Present draft content for review
    - Handle three resume actions: approve, edit, reject
    
    Responsibilities:
    - Interrupt workflow with approval payload
    - Handle resume actions (approve/edit/reject)
    - Update state with approved content
    - Route to appropriate next node based on action
    
    Architecture:
    - Uses LangGraph interrupt() for pause
    - Returns Command(goto=...) for routing
    - Immutable state updates
    - Structured error handling
    """
    
    def __call__(self, state: AgentState) -> Union[AgentState, Command]:
        """
        Execute human approval workflow.
        
        Args:
            state: Agent state containing draft_content
            
        Returns:
            Command for routing or updated state
        """
        log_agent_step("human_approval_node", state, "start")
        
        # Extract draft content with validation
        draft_raw = state.get("draft_content")
        draft_content = draft_raw if isinstance(draft_raw, str) else ""
        variants = self._extract_variants(state)
        if not draft_content and variants:
            draft_content = self._variant_to_text(variants["thought_leadership"])
        
        # Check if this is initial call or resume
        # On initial call, interrupt for human approval
        try:
            # Interrupt execution and request human approval
            approval_payload: Dict[str, Union[str, JSONValue]] = {
                "type": "approval_required",
                "draft": draft_content,
                "variants": variants,
            }
            
            # This will pause execution and return payload to user
            resume_value = interrupt(approval_payload)
            
            # After resume, handle the action
            action = self._extract_action(resume_value)
            
            log_agent_step("human_approval_node", {
                "action": action,
                "status": "resumed"
            }, "processing")
            
            if action == "approve":
                # Approve: use draft as-is
                selected_variant = self._extract_selected_variant(resume_value)
                approved_text = draft_content
                if selected_variant and selected_variant in variants:
                    approved_text = self._variant_to_text(variants[selected_variant])
                elif not approved_text and variants:
                    approved_text = self._variant_to_text(variants["thought_leadership"])
                return self._handle_approve(state, approved_text, selected_variant or "")
                
            elif action == "edit":
                # Edit: use edited text from resume value
                edited_text = self._extract_edited_text(resume_value)
                return self._handle_edit(state, edited_text)
                
            elif action == "reject":
                # Reject: go back to fetch_trends
                return self._handle_reject(state)
                
            else:
                # Unknown action: treat as approval
                log_agent_step("human_approval_node", {
                    "warning": f"Unknown action '{action}', treating as approve"
                }, "warning")
                return self._handle_approve(state, draft_content, "")
                
        except Exception as e:
            # Handle errors gracefully
            log_agent_step("human_approval_node", {
                "error": str(e),
                "status": "failed"
            }, "error")
            
            # Structured error
            error_info: Dict[str, Union[str, JSONValue]] = {
                "type": "human_approval_error",
                "message": str(e),
                "node": "human_approval"
            }
            
            # Return state with error (immutable)
            return {
                **state,
                "approved_content": draft_content,  # Fallback to draft
                "error": error_info
            }
    
    def _extract_action(self, resume_value: JSONValue) -> str:
        """
        Extract action from resume value.
        
        Args:
            resume_value: Value returned from interrupt resume
            
        Returns:
            Action string (approve/edit/reject)
        """
        if isinstance(resume_value, dict):
            action_raw = resume_value.get("action")
            return action_raw if isinstance(action_raw, str) else "approve"
        return "approve"
    
    def _extract_edited_text(self, resume_value: JSONValue) -> str:
        """
        Extract edited text from resume value.
        
        Args:
            resume_value: Value returned from interrupt resume
            
        Returns:
            Edited text string
        """
        if isinstance(resume_value, dict):
            edited_raw = resume_value.get("edited_text")
            return edited_raw if isinstance(edited_raw, str) else ""
        return ""
    
    def _extract_selected_variant(self, resume_value: JSONValue) -> str:
        if isinstance(resume_value, dict):
            selected_raw = resume_value.get("selected_variant")
            if isinstance(selected_raw, str):
                selected = selected_raw.strip()
                if selected in {"thought_leadership", "question_hook", "data_insight"}:
                    return selected
        return ""

    def _extract_variants(self, state: AgentState) -> Dict[str, Dict[str, JSONValue]]:
        gp = state.get("generated_posts") or {}
        if not isinstance(gp, dict):
            return {}
        out: Dict[str, Dict[str, JSONValue]] = {}
        for key in ("thought_leadership", "question_hook", "data_insight"):
            val = gp.get(key)
            if isinstance(val, dict):
                out[key] = val
        return out

    def _variant_to_text(self, variant: Dict[str, JSONValue]) -> str:
        body = str(variant.get("body") or "").strip()
        hashtags_raw = variant.get("hashtags") or []
        tags = []
        if isinstance(hashtags_raw, list):
            tags = [f"#{str(h).lstrip('#').strip()}" for h in hashtags_raw if str(h).strip()]
        text = f"{body}\n\n{' '.join(tags)}".strip()
        return text

    def _handle_approve(self, state: AgentState, draft_content: str, selected_variant: str) -> AgentState:
        """
        Handle approve action.
        
        Args:
            state: Current state
            draft_content: Draft content to approve
            
        Returns:
            Updated state with approved content
        """
        log_agent_step("human_approval_node", {
            "action": "approve",
            "status": "complete"
        }, "complete")
        
        # Return new state (immutable)
        return {
            **state,
            "approved_content": draft_content,
            "approved_for_publish": True,
            "publish_draft_text": draft_content,
            "selected_variant": selected_variant,
        }
    
    def _handle_edit(self, state: AgentState, edited_text: str) -> AgentState:
        """
        Handle edit action.
        
        Args:
            state: Current state
            edited_text: Edited text from user
            
        Returns:
            Updated state with edited content
        """
        log_agent_step("human_approval_node", {
            "action": "edit",
            "status": "complete"
        }, "complete")
        
        # Return new state (immutable)
        return {
            **state,
            "approved_content": edited_text,
            "approved_for_publish": True,
            "publish_draft_text": edited_text,
            "selected_variant": "",
        }
    
    def _handle_reject(self, state: AgentState) -> Command:
        """
        Handle reject action.
        
        Args:
            state: Current state
            
        Returns:
            Command to route back to fetch_trends
        """
        log_agent_step("human_approval_node", {
            "action": "reject",
            "status": "routing_back"
        }, "complete")
        
        # Route back to fetch_trends for retry
        return Command(goto="fetch_trends")
