#!/bin/bash

# Define models to test
models=(
    "gemini-2.5-flash-lite"
    "qwen3-max"
    "deepseek-v3.2"
    "gemini-2.5-pro"
)

echo "=== Starting Tool Calling Capability Test ==="
echo "API Endpoint: http://localhost:8317/v1/chat/completions"
echo "---------------------------------------------"

for model in "${models[@]}"; do
    echo -n "Testing model: $model ... "
    
    # Send request with tool definition
    response=$(curl -s -X POST http://localhost:8317/v1/chat/completions \
      -H "Content-Type: application/json" \
      -d '{
        "model": "'"$model"'",
        "messages": [
            {"role": "system", "content": "You are a data extraction assistant."},
            {"role": "user", "content": "Extract the entities: Dr. Sarah Connor works at Skynet."}
        ],
        "tools": [{
          "type": "function",
          "function": {
            "name": "extract_entities",
            "description": "Extract entities from text",
            "parameters": {
              "type": "object",
              "properties": {
                "entities": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "type": {"type": "string"}
                    },
                    "required": ["name", "type"]
                  }
                }
              },
              "required": ["entities"]
            }
          }
        }],
        "tool_choice": "auto"
      }')

    # Check output using python for robust JSON parsing
    result=$(echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'error' in data:
        print(f'ERROR: {data[\"error\"]}')
    elif 'choices' in data and data['choices'] and 'tool_calls' in data['choices'][0]['message'] and data['choices'][0]['message']['tool_calls']:
        tool_call = data['choices'][0]['message']['tool_calls'][0]
        args = tool_call['function']['arguments']
        print(f'SUCCESS [Args: {args[:50]}...]')
    else:
        content = data.get('choices', [{}])[0].get('message', {}).get('content', 'No content')
        print(f'FAILED (No tool call). Response: {content[:50]}...')
except Exception as e:
    print(f'CRASH: {e}')
")

    echo "$result"
done
echo "---------------------------------------------"
