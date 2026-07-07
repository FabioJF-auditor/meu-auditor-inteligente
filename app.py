def executar_chamada_gemini(prompt, imagens):
    """Executa a chamada usando uma estratégia de fallback para chaves corporativas"""
    try:
        conteudo_final = []
        conteudo_final.extend(imagens)
        conteudo_final.append(prompt)
        
        # Tentativa 1: Nome estável de produção exigido por contas Enterprise (2026)
        try:
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            response = model.generate_content(conteudo_final)
            return response.text
        except Exception as e_first:
            # Tentativa 2: Fallback caso a chave use a nomenclatura direta padrão
            if "404" in str(e_first) or "not found" in str(e_first).lower():
                model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
                response = model.generate_content(conteudo_final)
                return response.text
            else:
                raise e_first
                
    except Exception as e:
        return f"Falha na execução do processamento do Motor Estável Gemini: {e}"
