import os
from typing import List, Dict
import json
from openai import OpenAI
import aiohttp
from dotenv import load_dotenv
from text_service import TextSplitter, IDoc

load_dotenv()

taskId = "dokumenty"
dev_ai_api_key = os.getenv("DEV_AI_KEY")
client = OpenAI()
text_splitter = TextSplitter()

async def generate_keywords(text: str) -> List[str]:
    """Generuje słowa kluczowe w mianowniku dla danego tekstu"""
    prompt = """Wygeneruj listę słów kluczowych w mianowniku dla poniższego tekstu. 
    Słowa powinny być w formie podstawowej (np. "sportowiec" zamiast "sportowcem").
    Imię i nazwisko osoby powinno być w formie "Jan Kowalski" zamiast "Kowalski Jan".
    Imię i nazwisko osoby powinno być w formie "Jan Kowalski" zamiast "Jan, Kowalski".
    Keywoards powinny równiez posiadać polskie znaki diakrytyczne.
    Keywords powinny być w języku polskim.
    Keywords moze byc podany sektor, np. C4.
    Zwróć tylko listę słów, bez dodatkowego formatowania.
    Wykryj również relacje, np. "schwytanie nauczyciela".
    wydobądź informację o tym o kim jest każdy tekst. 

    <Przykłady>
    report-04, sektor 04, Barbara Zawadzka, frontend development, JavaScript, Python, sztuczna inteligencja, bazy wektorowe, walka wręcz, krav maga, broń palna, koktajle Mołotowa, pieczenie pizzy, ultradźwiękowy sygnał, nadajnik, odciski palców, las, zielone krzaki
    </Przykłady>
    Tekst:
    {text}
    """
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Jesteś ekspertem od generowania słów kluczowych w języku polskim."},
            {"role": "user", "content": prompt.format(text=text)}
        ],
        temperature=0.6,
    )
    
    keywords = response.choices[0].message.content.strip().split('\n')
    return [k.strip() for k in keywords if k.strip()]

async def combine_reports_and_facts(fileName: str, text: str, facts: List[str], keywords: List[str]) -> str:
    """Łączy tekst z faktami"""
    prompt = f"""
    Na podstawie poniższego tekstu oraz faktów, wygeneruj wspólną listę słów kluczowych. 
    Słowa powinny być w formie podstawowej (np. "sportowiec" zamiast "sportowcem").
    Imię i nazwisko osoby powinno być w formie "Jan Kowalski" zamiast "Kowalski Jan".
    Imię i nazwisko osoby powinno być w formie "Jan Kowalski" zamiast "Jan, Kowalski".
    Keywords powinny równiez posiadać polskie znaki diakrytyczne.
    Keywords powinny być w języku polskim.
    Keywords moze byc podany sektor, np. C4.
    Zwróć tylko listę słów, bez dodatkowego formatowania.
    Wykryj również relacje, np. "schwytanie nauczyciela".
    wydobądź informację o tym o kim jest każdy tekst. 
    Podawaj na podstawie nazwy pliku sektor np C4

    Nazwa pliku: {fileName}

    Tekst:
    {text}

    Fakty:
    {'\n\n '.join(facts)}

    Słowa kluczowe:
    {'\n\n '.join(keywords)}

    """
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Jesteś ekspertem od generowania słów kluczowych w języku polskim."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.6,
    )
    
    combined_keywords = response.choices[0].message.content.strip().split('\n')
    return [k.strip() for k in combined_keywords if k.strip()]


async def combine_keywords(sectors: Dict[str, List[str]], facts: List[Dict[str, List[str]]]) -> Dict[str, Dict[str, List[str]]]:
    """Łączy słowa kluczowe z sektorów i faktów, zwracając nazwy sektorów, pasujące fakty z nazwami plików i listę słów kluczowych pasujących do obu rzeczy"""
    combined_keywords = {}

    # Tworzymy zbiór wszystkich słów kluczowych z faktów
    all_fact_keywords = set()
    for fact in facts:
        if isinstance(fact, dict) and fact.get('keywords', []) is not []:
            all_fact_keywords.update(fact)

    # Dla każdego sektora, dodajemy pasujące słowa kluczowe z faktów i nazwe pliku z factem
    for sector_name, sector_keywords in sectors.items():
        matching_facts = [
            {"file_name": fact['file_name'], "keywords": fact['keywords']}
            for fact in facts if isinstance(fact, dict) and any(kw in fact.get('keywords', []) for kw in sector_keywords)
        ]
        combined_keywords[sector_name] = {
            "matching_facts": matching_facts,
            "keywords": list(set(sector_keywords) | 
                {kw for kw in all_fact_keywords if any(sk in kw or kw in sk for sk in sector_keywords)})
        }

    return combined_keywords


async def read_facts():
    facts = []
    facts_dir = os.path.join(os.path.dirname(__file__), "pliki_z_fabryki", "facts")
    if os.path.exists(facts_dir):
        for file in os.listdir(facts_dir):
            if file.endswith('.txt'):
                with open(os.path.join(facts_dir, file), 'r') as f:                
                    text = f.read()
                    if "entry deleted" in text:
                        continue
                    fact = await generate_keywords(text)
                    facts.append({"file_name": file, "keywords": fact})

    output_path = os.path.join(os.path.dirname(__file__), "keywords2.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(facts, f, ensure_ascii=False, indent=3)
    return facts

async def read_sectors():
    base_dir = os.path.join(os.path.dirname(__file__), "pliki_z_fabryki")
    keywords_dict = {}
    
    for file in os.listdir(base_dir):
        if not file.endswith('.txt'):
            continue
            
        file_path = os.path.join(base_dir, file)
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
            keywords = await generate_keywords(text)
            keywords_dict[file] = keywords
    
    output_path = os.path.join(os.path.dirname(__file__), "keywords1.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(keywords_dict, f, ensure_ascii=False, indent=2)
    
    return keywords_dict

async def read_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

async def main(has_chunks: bool = False):
    if has_chunks == False:
        facts = await read_facts()
        sectors = await read_sectors()
        
        # Łączymy słowa kluczowe z sektorów i faktów
        final_keywords = await combine_keywords(sectors, facts)
        
        # Zapisujemy końcowe słowa kluczowe do pliku
        final_keywords_path = os.path.join(os.path.dirname(__file__), "final_keywords.json")
        with open(final_keywords_path, 'w', encoding='utf-8') as f:
            json.dump(final_keywords, f, ensure_ascii=False, indent=4)
    else:
        # Odczytujemy końcowe słowa kluczowe z pliku
        final_keywords_path = os.path.join(os.path.dirname(__file__), "final_keywords.json")
        with open(final_keywords_path, 'r', encoding='utf-8') as f:
            final_keywords = json.load(f)
    
    answers = {}
    for file_name, data in final_keywords.items():
        with open(os.path.join(os.path.dirname(__file__), "pliki_z_fabryki", file_name), 'r', encoding='utf-8') as f:
            report_text = f.read()
        # combined_facts = await combine_reports_and_facts(data)
        
        # Odczytanie tekstów faktów z matching_facts
        matching_facts_texts = []
        all_keywords = data.get("keywords", [])
        for fact in data.get("matching_facts", []):
            with open(os.path.join(os.path.dirname(__file__), "pliki_z_fabryki", "facts", fact["file_name"]), 'r', encoding='utf-8') as f:
                fact_text = f.read()
                matching_facts_texts.append(fact_text)
                all_keywords = all_keywords + fact.get("keywords", [])

        combine = await combine_reports_and_facts(file_name, report_text, matching_facts_texts, all_keywords)
        answers[file_name] =  ", ".join(kw.strip() for kw in combine)


    with open(os.path.join(os.path.dirname(__file__), "formatted_keywords.json"), 'w', encoding='utf-8') as f:
        json.dump(answers, f, ensure_ascii=False, indent=2)
    
if __name__ == "__main__":
    import asyncio
    asyncio.run(main(has_chunks=True))

