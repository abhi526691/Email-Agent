from langchain_core.prompts import PromptTemplate
from .config import EMAIL_CLASSIFICATION_PROMPT, JOB_CATEGORIES

class EmailCategorizer:
    """Email categorizer using LLM Model defined by user."""
    
    def __init__(self, llm):
        self.llm = llm
        self.prompt_template = PromptTemplate(
            input_variables=["categories", "subject", "snippet"],
            template=EMAIL_CLASSIFICATION_PROMPT
        )
        # Use LCEL: Prompt | LLM
        self.chain = self.prompt_template | self.llm


    def categorize(self, emails):
        """Categorize a list of emails"""
        results = []
        categories_str = ", ".join(JOB_CATEGORIES.keys())

        for email in emails:
            subject = email.get("subject", "")
            snippet = email.get("snippet", "")
            try:
                # Use invoke instead of run
                response_msg = self.chain.invoke({
                    "subject": subject,
                    "snippet": snippet,
                    "categories": categories_str
                })
                
                # Handle response type (it might be a string or AIMessage)
                if hasattr(response_msg, 'content'):
                    response = response_msg.content.strip().lower()
                else:
                    response = str(response_msg).strip().lower()

                # match valid category or fallback
                category_key = (
                    response if response in JOB_CATEGORIES else "uncategorized"
                )
                label = JOB_CATEGORIES[category_key]["label"]

                email["category"] = category_key
                email["category_label"] = label
                results.append(email)

                try:
                    print(f"{subject[:60]} -> {label}")
                except UnicodeEncodeError:
                    print(f"{subject[:60].encode('ascii', 'replace').decode('ascii')} -> {label.encode('ascii', 'replace').decode('ascii')}")

            except Exception as e:
                print(f"Error classifying email '{subject}': {e}")

        return results

    def generate_reply(self, email_content, instructions=""):
        """Generate a reply to an email based on instructions"""
        try:
            from langchain_core.prompts import PromptTemplate
            
            reply_template = """
            You are a helpful email assistant. Draft a professional reply to the following email.
            
            Original Email:
            {email_content}
            
            Instructions for reply:
            {instructions}
            
            Draft Reply:
            """
            
            prompt = PromptTemplate(
                input_variables=["email_content", "instructions"],
                template=reply_template
            )
            
            chain = prompt | self.llm
            
            response_msg = chain.invoke({
                "email_content": email_content,
                "instructions": instructions
            })
            
            if hasattr(response_msg, 'content'):
                return response_msg.content.strip()
            else:
                return str(response_msg).strip()
                
        except Exception as e:
            print(f"Error generating reply: {e}")
            return "Error generating reply."
