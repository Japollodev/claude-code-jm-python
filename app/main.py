import argparse
import os
import sys
import json

from openai import OpenAI

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "Read",
            "description": "Read and return the contents of a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The path to the file to read"
                    }
                },
                "required": ["file_path"]
            }
        }
    }
]

def main():
    p = argparse.ArgumentParser()
    p.add_argument("-p", required=True)
    args = p.parse_args()

    messages = [{"role": "user", "content": args.p}]
    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")
    

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    while True:
        # Chat initiated
        chat = client.chat.completions.create(
            model="anthropic/claude-haiku-4.5",
            messages= messages,
            tools= TOOLS
        )
        # Create Boolean to check existing response choice
        has_chat_response = chat.choices and len(chat.choices) > 0

        # If not choice return error + break
        if not has_chat_response:
            raise RuntimeError("no choices in response")

        # Set response choice obj
        response_choice = chat.choices[0]
        # You can use print statements as follows for debugging, they'll be visible when running tests.
        print("Logs from your program will appear here!", file=sys.stderr)
        # Check if the response has a msg
        has_no_msg = response_choice.message is None 
        # If no msg exit
        if has_no_msg :
            print(response_choice, file=sys.stderr)
            break
        # Add message to messages
        messages.append(response_choice.message)
        tool_calls = response_choice.message.tool_calls
        # Check and ensure tool call exists
        if not tool_calls :
            sys.stdout.write(response_choice.message.content or "")
            break
        # Loop through the tool calls since they exist
        for tool in tool_calls:
            function_name = tool.function.name
            tool_id = tool.id
            # Handle Read tool calls
            if function_name is "Read" :
                try : 
                    function_args = json.loads(tool.function.arguments)
                    # Execute tool call on file path
                    with open(function_args["file_path"]) as file:
                        content = file.read()
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_id,
                            "content": content
                        })
                except Exception as e:
                    content = f"Error reading file: {e}"
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "content": content
                    })
            # Handle all other tool calls
            else :
                messages.append({
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "content": f"Unknown tool: {function_name}"
                    })




if __name__ is "__main__":
    main()
