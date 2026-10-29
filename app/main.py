import argparse
import os
import sys
import json

from openai import OpenAI

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-p", required=True)
    args = p.parse_args()
    user_input = ""
    messages = []
    sentinel = "exit"

    messages = []
    sentinel = "exit"

    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")
    

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    while not user_input  == sentinel:
        # Chat initiated
        chat = client.chat.completions.create(
            model="anthropic/claude-haiku-4.5",
            messages=[{"role": "user", "content": args.p}],
            tools=[
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
        )

        # Create Boolean to check existing response choice
        has_chat_response = chat.choices and len(chat.choices) > 0

        # If not choice return error + break
        if not has_chat_response:
            raise RuntimeError("no choices in response")
            break

        # Set response choice obj
        response_choice = chat.choices[0]
        # You can use print statements as follows for debugging, they'll be visible when running tests.
        print("Logs from your program will appear here!", file=sys.stderr)
        # Check if the response has a msg
        has_no_msg = response_choice.message == None 
        # If no msg exit
        if has_no_msg :
            print(response_choice, "<- has no message")
            break
        # Add message to messages
        messages.append(response_choice.message)
        tool_calls = response_choice.message.tool_calls
        has_tool_call = len(tool_calls) > 0 or tool_calls == None
        # Check and ensure tool call exists
        if not has_tool_call :
            sys.stdout.write(response_choice.message.content)
            break
        # Loop through the tool calls since they exist
        for tool in tool_calls:
            function_name = tool.function.name
            tool_id = tool.id
            if function_name == "Read" :
                function_args = json.loads(tool.function.arguments)
                try : 
                    with open(function_args["file_path"]) as file:
                        content = file.read()
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_id,
                            "content": content
                        })
                except Exception as e:
                    print(f"Error reading file: {e}", file=sys.stderr)



if __name__ == "__main__":
    main()
