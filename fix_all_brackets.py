with open('app.py', 'r') as f:
    content = f.read()

# Fix all the bracket issues in the questionnaire_steps structure
# Remove extra closing brackets on lines 284 and 296
# Add missing "id" fields and fix the structure

content = content.replace(
    '''                    ]}
                    ]
                },
                {
                    "question": "What's your current weight?"''',
    '''                    ]
                },
                {
                    "id": "weight",
                    "question": "What's your current weight?"'''
)

content = content.replace(
    '''                    ]}
                    ]
                },
                {
                    "id": "height",
                    "options": [''',
    '''                    ]
                },
                {
                    "id": "height",
                    "question": "How tall are you?",
                    "options": ['''
)

with open('app.py', 'w') as f:
    f.write(content)

print("Fixed all bracket issues in questionnaire_steps")
