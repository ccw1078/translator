# Prompt Template

```python
if include_vocabulary:
    system_prompt = "You are a professional Chinese-English translation assistant who is also skilled at extracting technical terms."
    user_prompt = f"""Please complete the following tasks:
        1. Accurately translate the following English text into Chinese.
        2. Extract 3-5 of the most important technical terms or key concepts from both the English text and its translation.
        3. Return format: First provide the Chinese translation, then add the special marker '===Technical terms===', followed by a JSON-formatted list of the extracted terms.


        English Text:{text}

        Example of vocabulary in JSON format:
        [{{
            \"english\": \"Machine Learning\",
            \"chinese\": \"机器学习\",
            \"explanation\": \"计算机通过数据自动学习而不依赖明确编程的技术\"
        }}]
        Please strictly follow the above format when returning the result, and do not add any extra explanations"""
else:
    system_prompt = "You are a professional Chinese-English translation assistant. Please accurately translate the English text provided by the user into Chinese. Return only the translation result, without adding any extra content."
    user_prompt = text
```

# Core Code

current Github project: [Translator](https://github.com/ccw1078/translator)

# Test Code

Tests folder of current project: [/tests](https://github.com/ccw1078/translator/tree/main/tests)

# Test Data and Word document samples

```
As you probably know, in my books I described what I call the Big Cycle in which 5 major forces--1) the debt/money order, 2) the internal political/social order, 3) the international geopolitical order, 4) acts of nature, and 5) new technologies--interact and transpire. I described in detail how these changes typically take place, and, as a result, I have many indicators that I watch closely to track how actual events are transpiring relative to my template. And, as you probably know, my measures show that we are now in the bubble stage of the Big Cycle, which is when there is unsustainable debt growth and monetization of the debts that change the monetary order and coincide with disruptive changes in the political, geopolitical, and technological orders
```

Word document sample: docs folder of current project

[/docs/translation_documents.docx](https://github.com/ccw1078/translator/blob/main/docs/translation_documents.docx)

# Operation Screenshots

![translate_with_vocabulary.png](https://lhwccw.oss-cn-shenzhen.aliyuncs.com/202511130855769.png)



# AI Conversation Records

Not available yet. It seems DeepSeek doesnt provide a sharing link for the conversation records. So I made a simple web demo to show the translation results, which is hosted on HuggingFace Spaces.


# Web Demo

> Due to Hugging Face's free-tier limitations, if an application receives no requests for an extended period, it may enter a sleep state. A cold restart takes some time, which can make the app appear unresponsive when first accessed.

web demo: [HuggingFace Space](https://huggingface.co/spaces/wwwtic/translator)

![](https://lhwccw.oss-cn-shenzhen.aliyuncs.com/202511130939830.png)

# TODO

- Consider adding streaming response functionality to return translation results in real time during the translation process if the text to be translated is very long, thereby improving user experience.  
- Consider implementing a translation history feature to allow users to easily view their previous translations.  
- Add validation and sanitization of API parameters to prevent injection of malicious or invalid inputs, enhancing the stability and security of the API.  
- Generated Word documents are temporarily stored on the server as static files for user download (to be periodically cleaned up). A more robust approach would be to upload them to cloud storage (e.g., Alibaba Cloud OSS).  
- In production environments, deploy the Flask application using Gunicorn to improve concurrency and performance. If the user base is large, consider migrating to the FastAPI framework to leverage its asynchronous capabilities and increase API throughput.

