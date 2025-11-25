"""
Document Processing Module
Handles extraction and chunking of various document types
"""
import os
import json
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup


class DocumentProcessor:
    """Process various document types and extract text content"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        Initialize document processor
        
        Args:
            chunk_size: Size of text chunks in characters
            chunk_overlap: Overlap between chunks in characters
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def process_file(self, file_path: str, file_type: str = None) -> Dict[str, Any]:
        """
        Process a file and extract its content
        
        Args:
            file_path: Path to the file
            file_type: File extension (auto-detected if None)
            
        Returns:
            Dictionary with content and metadata
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Auto-detect file type
        if file_type is None:
            file_type = Path(file_path).suffix.lower()
        
        # Remove leading dot from extension
        file_type = file_type.lstrip('.')
        
        # Extract content based on file type
        if file_type in ['md', 'txt']:
            content = self._process_text_file(file_path)
        elif file_type == 'json':
            content = self._process_json_file(file_path)
        elif file_type == 'html':
            content = self._process_html_file(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        # Create metadata
        metadata = {
            "source": os.path.basename(file_path),
            "file_type": file_type,
            "processed_at": datetime.now().isoformat(),
            "file_path": file_path
        }
        
        return {
            "content": content,
            "metadata": metadata
        }
    
    def _process_text_file(self, file_path: str) -> str:
        """Process plain text or markdown file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise Exception(f"Error reading text file: {str(e)}")
    
    def _process_json_file(self, file_path: str) -> str:
        """Process JSON file and convert to readable text"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Pretty print JSON for better readability
            return json.dumps(data, indent=2)
        except Exception as e:
            raise Exception(f"Error reading JSON file: {str(e)}")
    
    def _process_html_file(self, file_path: str) -> str:
        """
        Process HTML file - extract text and preserve structure
        Keeps element IDs, classes, and names for Selenium scripting
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract text content
            text_content = soup.get_text(separator='\n', strip=True)
            
            # Extract structural information for Selenium
            structural_info = self._extract_html_structure(soup)
            
            # Combine text and structural information
            full_content = f"HTML TEXT CONTENT:\n{text_content}\n\n"
            full_content += f"HTML STRUCTURE (Element IDs, Classes, Names):\n{structural_info}"
            
            return full_content
            
        except Exception as e:
            raise Exception(f"Error reading HTML file: {str(e)}")
    
    def _extract_html_structure(self, soup: BeautifulSoup) -> str:
        """Extract HTML element structure with IDs, classes, and names"""
        structure_lines = []
        
        # Find all elements with id
        elements_with_id = soup.find_all(id=True)
        if elements_with_id:
            structure_lines.append("Elements with ID:")
            for elem in elements_with_id:
                elem_info = f"  - {elem.name}#{elem.get('id')}"
                if elem.get('class'):
                    elem_info += f" .{'.'.join(elem.get('class'))}"
                if elem.get('name'):
                    elem_info += f" [name='{elem.get('name')}']"
                structure_lines.append(elem_info)
        
        # Find all form inputs with name
        inputs = soup.find_all(['input', 'select', 'textarea'], attrs={'name': True})
        if inputs:
            structure_lines.append("\nForm Inputs:")
            for inp in inputs:
                inp_type = inp.get('type', 'text')
                inp_info = f"  - {inp.name}[name='{inp.get('name')}']"
                if inp.get('id'):
                    inp_info += f" id='{inp.get('id')}'"
                inp_info += f" type='{inp_type}'"
                structure_lines.append(inp_info)
        
        # Find all buttons
        buttons = soup.find_all(['button', 'input'])
        clickable_buttons = [b for b in buttons if b.name == 'button' or b.get('type') in ['submit', 'button']]
        if clickable_buttons:
            structure_lines.append("\nButtons:")
            for btn in clickable_buttons:
                btn_info = f"  - {btn.name}"
                if btn.get('id'):
                    btn_info += f" id='{btn.get('id')}'"
                if btn.get('onclick'):
                    btn_info += f" onclick='{btn.get('onclick')[:50]}...'"
                structure_lines.append(btn_info)
        
        return '\n'.join(structure_lines) if structure_lines else "No structural elements found"
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Text to chunk
            
        Returns:
            List of text chunks
        """
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # If not at the end, try to break at a sentence or word boundary
            if end < len(text):
                # Look for sentence boundary (. ! ?)
                sentence_end = max(
                    text.rfind('. ', start, end),
                    text.rfind('! ', start, end),
                    text.rfind('? ', start, end)
                )
                
                if sentence_end > start:
                    end = sentence_end + 1
                else:
                    # Look for word boundary
                    space_pos = text.rfind(' ', start, end)
                    if space_pos > start:
                        end = space_pos
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - self.chunk_overlap
            if start >= len(text):
                break
        
        return chunks
    
    def process_and_chunk(self, file_path: str, file_type: str = None) -> List[Dict[str, Any]]:
        """
        Process file and split into chunks
        
        Args:
            file_path: Path to file
            file_type: File extension
            
        Returns:
            List of document chunks with metadata
        """
        # Process file
        doc = self.process_file(file_path, file_type)
        
        # Chunk the content
        chunks = self.chunk_text(doc['content'])
        
        # Create document chunks with metadata
        chunk_docs = []
        for i, chunk in enumerate(chunks):
            chunk_doc = {
                'content': chunk,
                'metadata': {
                    **doc['metadata'],
                    'chunk_id': i,
                    'total_chunks': len(chunks)
                }
            }
            chunk_docs.append(chunk_doc)
        
        return chunk_docs
    
    def process_directory(self, directory_path: str) -> List[Dict[str, Any]]:
        """
        Process all supported files in a directory
        
        Args:
            directory_path: Path to directory
            
        Returns:
            List of all document chunks
        """
        supported_extensions = ['.md', '.txt', '.json', '.html']
        all_chunks = []
        
        for root, _, files in os.walk(directory_path):
            for file in files:
                file_ext = Path(file).suffix.lower()
                if file_ext in supported_extensions:
                    file_path = os.path.join(root, file)
                    try:
                        chunks = self.process_and_chunk(file_path)
                        all_chunks.extend(chunks)
                        print(f"Processed: {file} ({len(chunks)} chunks)")
                    except Exception as e:
                        print(f"Error processing {file}: {str(e)}")
        
        return all_chunks


if __name__ == "__main__":
    # Test the document processor
    processor = DocumentProcessor()
    
    # Test with a sample text
    sample_text = "This is a test document. " * 100
    chunks = processor.chunk_text(sample_text)
    print(f"Created {len(chunks)} chunks from sample text")
    print(f"First chunk length: {len(chunks[0])}")
    print(f"Last chunk length: {len(chunks[-1])}")