import tiktoken

enc = tiktoken.get_encoding("cl100k_base")

def token_len(text: str) -> int:
    return len(enc.encode(text))

def recursive_chunk(text: str, chunk_size: int = 10, overlap: int = 20) -> list[str]:
    separators = ["\n\n", "\n", ". ", " ", ""]
    
    def split(text, separators):
        if token_len(text) <= chunk_size:
            return [text]  # fits, no need to split
        
        if not separators:
            # last resort: brute force by tokens
            tokens = enc.encode(text)
            chunks = []
            start = 0
            while start < len(tokens):
                end = start + chunk_size
                chunks.append(enc.decode(tokens[start:end]))
                start += chunk_size - overlap
            return chunks
        
        sep = separators[0]
        parts = text.split(sep)
        
        chunks = []
        current = ""
        
        for part in parts:
            candidate = current + sep + part if current else part
            
            if token_len(candidate) <= chunk_size:
                current = candidate  # still fits, keep building
            else:
                if current:
                    chunks.append(current)  # save what we have
                # this part alone might still be too big → recurse
                if token_len(part) > chunk_size:
                    chunks.extend(split(part, separators[1:]))
                    current = ""
                else:
                    current = part
        
        if current:
            chunks.append(current)
        
        return chunks
    
    return split(text, separators)



result = recursive_chunk("The vendor is ABC Corp. Contact them at abc@corp.com. They are based in Karachi.")
print(result)