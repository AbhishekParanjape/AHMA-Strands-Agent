#!/usr/bin/env python3
"""
Simple test to verify PDF tools are working in the superagent
"""

from superagent_test import router_agent

def test_pdf_tools():
    """Test PDF tools recognition and functionality."""
    print("🧪 Testing PDF tools in superagent...")
    
    # Check available tools
    print(f"\n📋 Available tools ({len(router_agent.tools)}):")
    for i, tool in enumerate(router_agent.tools, 1):
        tool_name = tool.__name__
        print(f"  {i}. {tool_name}")
    
    # Check for PDF tools specifically
    pdf_tools = [tool for tool in router_agent.tools if 'pdf' in tool.__name__.lower() or 'fill' in tool.__name__.lower()]
    print(f"\n📄 PDF-related tools found: {len(pdf_tools)}")
    for tool in pdf_tools:
        print(f"  - {tool.__name__}")
    
    # Test PDF tool recognition with various prompts
    test_prompts = [
        "Fill up my health-declaration-form.pdf",
        "Process the insurance form",
        "Fill out the medical claim",
        "List PDF files",
        "Show me available PDF forms"
    ]
    
    print(f"\n🧪 Testing PDF tool recognition...")
    for prompt in test_prompts:
        print(f"\nPrompt: '{prompt}'")
        try:
            # This will show which tool the agent would use
            response = router_agent(prompt)
            print(f"Response: {response[:150]}...")
        except Exception as e:
            print(f"Error: {e}")
    
    print(f"\n🎯 Total tools: {len(router_agent.tools)}")
    print(f"🎯 PDF tools: {len(pdf_tools)}")
    
    if len(pdf_tools) >= 4:
        print("✅ PDF tools are properly integrated!")
        return True
    else:
        print("❌ PDF tools are not properly integrated")
        return False

if __name__ == "__main__":
    test_pdf_tools()
