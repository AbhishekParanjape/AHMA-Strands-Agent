"""
Ultravox integration endpoints for AHMA Flutter app
"""
from flask import jsonify, request
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
        """
        Handle tool requests from Ultravox during live calls.
        This is called when the agent invokes a custom tool that points to this backend.
        """
        try:
            data = request.get_json(silent=True) or {}

            tool_name = data.get('toolName')
            parameters = data.get('parameters', {})
            call_id = data.get('callId')

            if not tool_name:
                return jsonify({
                    'success': False,
                    'error': 'Missing toolName'
                }), 400

            print(f"🔧 [Ultravox] Tool request: {tool_name}")
            print(f"   Call: {call_id}")
            print(f"   Parameters: {parameters}")

            # Route to appropriate tool handler
            if tool_name == 'schedule_reminder':
                result = _handle_schedule_reminder(parameters)
            elif tool_name == 'create_mental_health_block':
                result = _handle_mental_health_block(parameters)
            elif tool_name == 'save_resource':
                result = _handle_save_resource(parameters)
            else:
                result = {
                    'success': False,
                    'message': f'Unknown tool: {tool_name}'
                }

            print(f"✅ [Ultravox] Tool executed: {result}")

            return jsonify(result)

        except Exception as e:
            print(f"❌ [Ultravox] Error handling tool request: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500


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


def _handle_schedule_reminder(parameters):
    """Handle scheduling a reminder via Google Calendar"""
    # TODO: Integrate with google_calendar_service
    print(f"📅 Scheduling reminder: {parameters}")
    return {
        'success': True,
        'message': 'Reminder scheduled',
        'parameters': parameters,
    }


def _handle_mental_health_block(parameters):
    """Handle creating mental health time blocks"""
    # TODO: Integrate with google_calendar_service
    print(f"🧘 Creating mental health block: {parameters}")
    return {
        'success': True,
        'message': 'Mental health time blocked',
        'parameters': parameters,
    }


def _handle_save_resource(parameters):
    """Handle saving a resource recommendation"""
    # TODO: Save to database or send to Flutter
    print(f"💾 Saving resource: {parameters}")
    return {
        'success': True,
        'message': 'Resource saved',
        'parameters': parameters,
    }
