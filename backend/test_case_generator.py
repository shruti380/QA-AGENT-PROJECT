"""
Test Case Generator using RAG and LLM
"""
import json
from typing import List, Dict, Any, Optional
from backend.vector_store import VectorStore
from backend.groq_client import GroqClient


class TestCaseGenerator:
    """Generate test cases using RAG and LLM"""
    
    def __init__(self, vector_store: VectorStore, llm_client: GroqClient):
        """
        Initialize test case generator
        
        Args:
            vector_store: Vector store for document retrieval
            llm_client: LLM client for generation
        """
        self.vector_store = vector_store
        self.llm_client = llm_client
        
        self.system_prompt = """You are an expert QA engineer. Generate test cases based STRICTLY on the provided documentation.

CRITICAL RULES:
1. Only create test cases for features explicitly mentioned in the documents
2. Every test case MUST reference its source document in the "grounded_in" field
3. Do not invent, assume, or hallucinate any features not in the documents
4. Include both positive and negative test scenarios when appropriate
5. Be specific about expected results
6. Use actual values from the documentation (prices, discount codes, etc.)

Output format - Return a JSON array of test cases:
[
  {
    "test_id": "TC-001",
    "feature": "Discount Code",
    "test_scenario": "Apply valid discount code SAVE15",
    "test_type": "positive",
    "test_steps": [
      "Add items to cart totaling $100",
      "Enter discount code 'SAVE15' in discount field",
      "Click 'Apply' button"
    ],
    "expected_result": "Discount of 15% ($15) is applied, total price shows $85 plus tax",
    "grounded_in": "product_specs.md: 'SAVE15 applies 15% discount on total order'"
  }
]

Remember: 
- Only facts from the provided documents
- Always cite the source in "grounded_in"
- Be precise and testable
- No assumptions or invented features
"""
    
    def generate_test_cases(
        self, 
        user_query: str, 
        html_content: Optional[str] = None,
        num_results: int = 10,
        top_k_docs: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Generate test cases based on user query using RAG
        
        Args:
            user_query: User's request for test cases
            html_content: Optional HTML content for context
            num_results: Number of test cases to generate
            top_k_docs: Number of documents to retrieve from vector store
            
        Returns:
            List of test case dictionaries
        """
        # Retrieve relevant context from vector store
        print(f"Retrieving relevant documents for: {user_query}")
        search_results = self.vector_store.similarity_search(user_query, k=top_k_docs)
        
        if not search_results:
            raise Exception("No relevant documentation found. Please build the knowledge base first.")
        
        # Build context from retrieved documents
        context = self._build_context(search_results)
        
        # Add HTML structure if provided
        if html_content:
            context += f"\n\nHTML STRUCTURE AVAILABLE:\n{html_content[:1000]}..."
        
        # Build prompt
        prompt = f"""Based on the following documentation, generate {num_results} test cases for: {user_query}

DOCUMENTATION:
{context}

USER REQUEST: {user_query}

Generate exactly {num_results} test cases in JSON array format. Each test case must:
1. Have a unique test_id (TC-001, TC-002, etc.)
2. Reference the feature being tested
3. Clearly describe the test scenario
4. Specify test_type as "positive" or "negative"
5. List detailed test_steps as an array
6. State the expected_result clearly
7. Include "grounded_in" field citing the exact source document and relevant quote

Return ONLY the JSON array, no other text."""
        
        # Generate test cases
        print("Generating test cases with LLM...")
        try:
            response = self.llm_client.generate_structured(
                prompt=prompt,
                system_prompt=self.system_prompt,
                temperature=0.5,
                max_tokens=4000
            )
            
            # Validate response
            if isinstance(response, list):
                test_cases = response
            elif isinstance(response, dict) and 'test_cases' in response:
                test_cases = response['test_cases']
            else:
                raise Exception("Invalid response format from LLM")
            
            # Validate and clean test cases
            validated_cases = self._validate_test_cases(test_cases)
            
            print(f"Generated {len(validated_cases)} test cases")
            return validated_cases
            
        except Exception as e:
            raise Exception(f"Error generating test cases: {str(e)}")
    
    def _build_context(self, search_results: List[Dict[str, Any]]) -> str:
        """Build context string from search results"""
        context_parts = []
        
        for i, result in enumerate(search_results):
            source = result['metadata'].get('source', 'unknown')
            content = result['content']
            
            context_parts.append(f"[Source: {source}]\n{content}\n")
        
        return "\n".join(context_parts)
    
    def _validate_test_cases(self, test_cases: List[Dict]) -> List[Dict[str, Any]]:
        """Validate and clean test cases"""
        required_fields = ['test_id', 'feature', 'test_scenario', 'test_steps', 'expected_result', 'grounded_in']
        validated = []
        
        for i, tc in enumerate(test_cases):
            # Check required fields
            if not all(field in tc for field in required_fields):
                print(f"Warning: Test case {i} missing required fields, skipping")
                continue
            
            # Ensure test_steps is a list
            if isinstance(tc['test_steps'], str):
                tc['test_steps'] = [tc['test_steps']]
            
            # Add test_type if missing
            if 'test_type' not in tc:
                tc['test_type'] = 'positive'
            
            # Validate grounding
            if not tc['grounded_in'] or tc['grounded_in'] == '':
                print(f"Warning: Test case {tc['test_id']} has no grounding reference")
            
            validated.append(tc)
        
        return validated
    
    def generate_specific_test_case(
        self,
        feature: str,
        test_type: str = "positive",
        context_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a specific test case for a feature
        
        Args:
            feature: Feature name to test
            test_type: "positive" or "negative"
            context_query: Optional query to retrieve specific context
            
        Returns:
            Single test case dictionary
        """
        query = context_query or f"test {test_type} scenario for {feature}"
        
        search_results = self.vector_store.similarity_search(query, k=5)
        context = self._build_context(search_results)
        
        prompt = f"""Generate a single {test_type} test case for: {feature}

DOCUMENTATION:
{context}

Create ONE detailed test case in JSON format with:
- test_id
- feature: "{feature}"
- test_scenario
- test_type: "{test_type}"
- test_steps (array)
- expected_result
- grounded_in (cite the source)

Return ONLY the JSON object."""
        
        response = self.llm_client.generate_structured(
            prompt=prompt,
            system_prompt=self.system_prompt,
            temperature=0.4
        )
        
        # Handle response
        if isinstance(response, list) and len(response) > 0:
            test_case = response[0]
        elif isinstance(response, dict):
            test_case = response
        else:
            raise Exception("Invalid response format")
        
        # Validate
        validated = self._validate_test_cases([test_case])
        return validated[0] if validated else None


def test_generator():
    """Test the test case generator"""
    from backend.vector_store import VectorStore
    from backend.groq_client import GroqClient
    
    print("Testing Test Case Generator...")
    
    # Create mock vector store
    vs = VectorStore(index_path="test_vector_db")
    
    # Add sample documents
    sample_docs = [
        {
            'content': 'Discount code SAVE15 applies 15% discount on total order. No minimum order required.',
            'metadata': {'source': 'product_specs.md'}
        },
        {
            'content': 'Minimum order amount is $50. Orders below this amount cannot be processed.',
            'metadata': {'source': 'product_specs.md'}
        }
    ]
    vs.add_documents(sample_docs)
    
    # Create LLM client
    llm = GroqClient()
    
    # Create generator
    generator = TestCaseGenerator(vs, llm)
    
    # Generate test cases
    try:
        test_cases = generator.generate_test_cases(
            user_query="Generate test cases for discount code feature",
            num_results=2
        )
        
        print(f"\nGenerated {len(test_cases)} test cases:")
        for tc in test_cases:
            print(f"\n{tc['test_id']}: {tc['test_scenario']}")
            print(f"  Grounded in: {tc['grounded_in']}")
    
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    test_generator()