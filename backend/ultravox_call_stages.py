"""
Ultravox integration endpoints for AHMA Flutter app
"""
from flask import jsonify, request, make_response
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from superagent_test import router_agent


def register_ultravox_routes(app):
    """Register Ultravox integration routes"""

    @app.route('/api/ultravox/transcript', methods=['POST'])
    def receive_transcript():
        """
        Receive call transcript from Flutter app after Ultravox call ends.
        Process it through the router agent to trigger appropriate actions.
        """
        try:
            data = request.get_json(silent=True) or {}

            call_id = data.get('callId')
            user_id = data.get('userId')
            transcript = data.get('transcript', [])
            stress_level = data.get('stressLevel', 'regular')
            metadata = data.get('metadata', {})

            if not call_id or not transcript:
                return jsonify({
                    'success': False,
                    'error': 'Missing callId or transcript'
                }), 400

            print(f"📝 [Ultravox] Received transcript for call {call_id}")
            print(f"   User: {user_id}, Stress: {stress_level}")
            print(f"   Messages: {len(transcript)}")

            # Build conversation summary for router agent
            conversation_text = _format_transcript(transcript)

            # Create context for the agent
            agent_prompt = f"""
            Process this caregiver voice conversation and take appropriate actions:

            Stress Level: {stress_level}
            Conversation:
            {conversation_text}

            Based on this conversation:
            1. If the caregiver needs calendar reminders or mental health time blocks, create them
            2. If specific resources were mentioned, ensure they're saved
            3. Generate a brief action plan for next steps
            4. If tasks were identified, create them in Todoist

            Provide a summary of actions taken.
            """

            # Process with router agent
            result = router_agent(agent_prompt)

            # Extract result text
            result_text = _extract_text(result)

            print(f"✅ [Ultravox] Processed transcript, actions: {result_text[:100]}...")

            # TODO: Send webhook back to Flutter app with results
            # For now, just log the result

            return jsonify({
                'success': True,
                'message': 'Transcript processed',
                'callId': call_id,
                'actions': result_text,
            })

        except Exception as e:
            print(f"❌ [Ultravox] Error processing transcript: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500


    @app.route('/api/ultravox/tool-request', methods=['POST'])
    def handle_tool_request():
        try:
            data = request.get_json(silent=True) or {}
            tool_name = data.get('toolName')
            parameters = data.get('parameters', {})
            
            # --------------------------------------------------------
            # NEW: Handle Ultravox Call Stages
            # --------------------------------------------------------
            if tool_name == 'change_conversation_stage':
                target_stage = parameters.get('target_stage')
                print(f"🔄 [Ultravox] Transitioning to stage: {target_stage}")
                
                new_prompt = ""
                new_tools = [] # Define whichever tools are relevant for the new stage
                
                # Flowchart Branch 1: Scheduling
                if target_stage == 'scheduling':
                    new_prompt = """
                    STAGE: Scheduling
                    The user wants to schedule a task or event. 
                    Your goal: Probe for more info on the details of follow-ups (time, date, context).
                    Once the user provides all necessary fields, invoke the 'create_task_event' tool.
                    """
                    # You would define the 'create_task_event' tool in your Ultravox dashboard or initialization

                # Flowchart Branch 2: Feelings
                elif target_stage == 'feelings':
                    new_prompt = """
                    STAGE: Sharing feelings/events
                    Your goal: Validate the user's feelings and probe for more context.
                    - If the user feels better and is ready for follow-up actions, use the 'change_conversation_stage' tool with target_stage="scheduling".
                    - If the user feels better but still seems lost/asks for extra help, use the 'change_conversation_stage' tool with target_stage="resources".
                    """
                    
                # Flowchart Branch 3: Resources
                elif target_stage == 'resources':
                    new_prompt = """
                    STAGE: Resources
                    The user is looking for resources or support.
                    Your goal: Probe for more info on what the user is struggling with.
                    Once the user gives enough specific context (not too much needed), use the 'redirect_to_resources' tool to provide relevant support groups or generated reports.
                    """

                # Build the response body for the new stage
                response_body = {
                    "systemPrompt": new_prompt,
                    "toolResultText": f"(New Stage) Transitioned to {target_stage}. Acknowledge and proceed."
                    # Note: You can also pass "selectedTools" here if you only want specific tools available in certain stages
                }
                
                # MUST return this specific header for Ultravox to trigger a stage change
                resp = make_response(jsonify(response_body))
                resp.headers['X-Ultravox-Response-Type'] = 'new-stage'
                return resp

            # --------------------------------------------------------
            # Existing Terminal Tools (Action nodes at bottom of flowchart)
            # --------------------------------------------------------
            elif tool_name == 'create_task_event':
                # Handle creating the event
                return jsonify({'success': True, 'message': 'Task created'})
                
            elif tool_name == 'redirect_to_resources':
                # Handle fetching resources
                return jsonify({'success': True, 'resources': ['Support Group A', 'Burnout Report']})

            else:
                return jsonify({'success': False, 'message': f'Unknown tool: {tool_name}'})

        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500


    @app.route('/api/flutter/webhook/register', methods=['POST'])
    def register_flutter_webhook():
    """
    Register Flutter app webhook endpoint to receive async updates.
    Store the webhook URL for the user.
    """
    try:
        data = request.get_json(silent=True) or {}

        user_id = data.get('userId')
        webhook_url = data.get('webhookUrl')

        if not user_id or not webhook_url:
            return jsonify({
                'success': False,
                'error': 'Missing userId or webhookUrl'
            }), 400

        # TODO: Store webhook URL in database/cache
        # For POC, just log it
        print(f"📱 [Flutter] Registered webhook for user {user_id}: {webhook_url}")

        return jsonify({
            'success': True,
            'message': 'Webhook registered',
            'userId': user_id,
        })

    except Exception as e:
        print(f"❌ [Flutter] Error registering webhook: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Helper functions

def _format_transcript(transcript):
    """Format transcript messages into readable text"""
    lines = []
    for msg in transcript:
        role = msg.get('role', 'unknown')
        text = msg.get('text', '')
        speaker = "Caregiver" if role == 'user' else "AHMA"
        lines.append(f"{speaker}: {text}")
    return "\n".join(lines)


def _extract_text(result):
    """Extract text from agent result (same logic as main app.py)"""
    if isinstance(result, str):
        return result

    # Handle AgentResult-like objects
    if hasattr(result, 'message') and hasattr(result, 'stop_reason'):
        message = result.message
        if isinstance(message, dict):
            if message.get("role") == "assistant" and "content" in message:
                content = message["content"]
                if isinstance(content, list) and len(content) > 0:
                    first_item = content[0]
                    if isinstance(first_item, dict) and "text" in first_item:
                        return first_item["text"]

    return str(result)

