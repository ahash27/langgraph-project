"""Human approval node - pauses execution for human review using LangGraph interrupt"""

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
        
        # Check if this is initial call or resume
        # On initial call, interrupt for human approval
        try:
            # Interrupt execution and request human approval
            approval_payload: Dict[str, Union[str, JSONValue]] = {
                "type": "approval_required",
                "draft": draft_content
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
                return self._handle_approve(state, draft_content)
                
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
                return self._handle_approve(state, draft_content)
                
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
    
    def _handle_approve(self, state: AgentState, draft_content: str) -> AgentState:
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
            "approved_content": draft_content
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
            "approved_content": edited_text
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
