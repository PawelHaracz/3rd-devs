from typing import Dict, List, Tuple, Optional
import tiktoken  # Zmiana importu

class IDoc:
    def __init__(self, text: str, metadata: Dict):
        self.text = text
        self.metadata = metadata


class TextSplitter:
    def __init__(self, model_name: str = 'gpt-4o'):
        self.tokenizer = None
        self.MODEL_NAME = model_name
        self.SPECIAL_TOKENS = {
            '<|im_start|>': 100264,
            '<|im_end|>': 100265,
            '<|im_sep|>': 100266,
        }

    async def initialize_tokenizer(self) -> None:
        if not self.tokenizer:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")  # Zmiana inicjalizacji tokenizera

    def count_tokens(self, text: str) -> int:
        if not self.tokenizer:
            raise Exception('Tokenizer not initialized')
        formatted_content = self.format_for_tokenization(text)
        # Specjalne tokeny są już obsługiwane przez cl100k_base, więc nie musimy ich przekazywać
        tokens = self.tokenizer.encode(formatted_content)
        return len(tokens)

    def format_for_tokenization(self, text: str) -> str:
        return f"<|im_start|>user\n{text}<|im_end|>\n<|im_start|>assistant<|im_end|>"

    async def split(self, text: str, limit: int) -> List[IDoc]:
        print(f"Starting split process with limit: {limit} tokens")
        await self.initialize_tokenizer()
        chunks: List[IDoc] = []
        position = 0
        total_length = len(text)
        current_headers: Dict[str, List[str]] = {}

        while position < total_length:
            print(f"Processing chunk starting at position: {position}")
            chunk_result = self.get_chunk(text, position, limit)
            chunk_text, chunk_end = chunk_result['chunk_text'], chunk_result['chunk_end']
            tokens = self.count_tokens(chunk_text)
            print(f"Chunk tokens: {tokens}")

            headers_in_chunk = self.extract_headers(chunk_text)
            self.update_current_headers(current_headers, headers_in_chunk)

            content_result = self.extract_urls_and_images(chunk_text)
            content, urls, images = content_result['content'], content_result['urls'], content_result['images']

            chunks.append(IDoc(
                text=content,
                metadata={
                    'tokens': tokens,
                    'headers': dict(current_headers),
                    'urls': urls,
                    'images': images,
                }
            ))

            print(f"Chunk processed. New position: {chunk_end}")
            position = chunk_end

        print(f"Split process completed. Total chunks: {len(chunks)}")
        return chunks

    def get_chunk(self, text: str, start: int, limit: int) -> Dict[str, any]:
        print(f"Getting chunk starting at {start} with limit {limit}")
        
        overhead = self.count_tokens(self.format_for_tokenization('')) - self.count_tokens('')
        
        end = min(start + int((len(text) - start) * limit / self.count_tokens(text[start:])), len(text))
        
        chunk_text = text[start:end]
        tokens = self.count_tokens(chunk_text)
        
        while tokens + overhead > limit and end > start:
            print(f"Chunk exceeds limit with {tokens + overhead} tokens. Adjusting end position...")
            end = self.find_new_chunk_end(text, start, end)
            chunk_text = text[start:end]
            tokens = self.count_tokens(chunk_text)

        end = self.adjust_chunk_end(text, start, end, tokens + overhead, limit)
        
        chunk_text = text[start:end]
        tokens = self.count_tokens(chunk_text)
        print(f"Final chunk end: {end}")
        return {'chunk_text': chunk_text, 'chunk_end': end}

    def adjust_chunk_end(self, text: str, start: int, end: int, current_tokens: int, limit: int) -> int:
        min_chunk_tokens = limit * 0.8

        next_newline = text.find('\n', end)
        prev_newline = text.rfind('\n', 0, end)

        if next_newline != -1 and next_newline < len(text):
            extended_end = next_newline + 1
            chunk_text = text[start:extended_end]
            tokens = self.count_tokens(chunk_text)
            if tokens <= limit and tokens >= min_chunk_tokens:
                print(f"Extending chunk to next newline at position {extended_end}")
                return extended_end

        if prev_newline > start:
            reduced_end = prev_newline + 1
            chunk_text = text[start:reduced_end]
            tokens = self.count_tokens(chunk_text)
            if tokens <= limit and tokens >= min_chunk_tokens:
                print(f"Reducing chunk to previous newline at position {reduced_end}")
                return reduced_end

        return end

    def find_new_chunk_end(self, text: str, start: int, end: int) -> int:
        new_end = end - int((end - start) / 10)
        if new_end <= start:
            new_end = start + 1
        return new_end

    def extract_headers(self, text: str) -> Dict[str, List[str]]:
        headers: Dict[str, List[str]] = {}
        import re
        header_regex = r'(^|\n)(#{1,6})\s+(.*)'
        
        for match in re.finditer(header_regex, text):
            level = len(match.group(2))
            content = match.group(3).strip()
            key = f'h{level}'
            if key not in headers:
                headers[key] = []
            headers[key].append(content)
        
        return headers

    def update_current_headers(self, current: Dict[str, List[str]], extracted: Dict[str, List[str]]) -> None:
        for level in range(1, 7):
            key = f'h{level}'
            if key in extracted:
                current[key] = extracted[key]
                self.clear_lower_headers(current, level)

    def clear_lower_headers(self, headers: Dict[str, List[str]], level: int) -> None:
        for l in range(level + 1, 7):
            key = f'h{l}'
            if key in headers:
                del headers[key]

    def extract_urls_and_images(self, text: str) -> Dict[str, any]:
        urls: List[str] = []
        images: List[str] = []
        url_index = 0
        image_index = 0
        import re

        def replace_images(match):
            nonlocal image_index
            alt_text, url = match.groups()
            images.append(url)
            result = f'![{alt_text}]({{$img{image_index}}})'
            image_index += 1
            return result

        def replace_urls(match):
            nonlocal url_index
            link_text, url = match.groups()
            urls.append(url)
            result = f'[{link_text}]({{$url{url_index}}})'
            url_index += 1
            return result

        content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', replace_images, text)
        content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replace_urls, content)

        return {'content': content, 'urls': urls, 'images': images} 