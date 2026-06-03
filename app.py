import streamlit as st
import pdfplumber
import pandas as pd
import re
import pytesseract

# Configuração da página da App
st.set_page_config(page_title="Extrator de Faturas", layout="centered")
st.title("🧾 Extrator Rápido de Faturas")
st.write("Extrai a Data, Número de Cliente, Número da Fatura e Valor.")

ficheiro_carregado = st.file_uploader("Arraste o ficheiro PDF aqui", type=["pdf"])

if ficheiro_carregado is not None:
    if st.button("Extrair Dados"):
        with st.spinner("A analisar o PDF e a ler marcas de água... Isto pode demorar uns segundos."):
            dados = []
            
            padrao_fatura = r"Fatura N\.º\s+(.+)"
            padrao_data = r"Data de Emissão:\s+(\d{2}-\d{2}-\d{4})"
            
            with pdfplumber.open(ficheiro_carregado) as pdf:
                for pagina in pdf.pages:
                    texto = pagina.extract_text()
                    
                    if not texto:
                        continue
                        
                    fatura_match = re.search(padrao_fatura, texto)
                    data_match = re.search(padrao_data, texto)
                    
                    if fatura_match:
                        
                        # 1. Extrair o Valor Normal
                        valor_match = re.search(r"Total a pagar[\s\S]*?([\d.,]+€)", texto)
                        valor_normal = valor_match.group(1).strip() if valor_match else "N/D"

                        # 2. IA para detetar o desenho da marca de água "ANULADA"
                        try:
                            # Tira uma "fotografia" da página para conseguir ler os carimbos
                            imagem = pagina.to_image(resolution=100).original
                            texto_imagem = pytesseract.image_to_string(imagem).lower()
                            
                            # Se a IA ler "anulad" algures na fotografia, força o 0,00€
                            if "anulad" in texto_imagem:
                                valor = "0,00€"
                            else:
                                valor = valor_normal
                        except Exception:
                            # Prevenção: Se a IA falhar a carregar no site, não bloqueia o programa e usa o valor normal
                            valor = valor_normal

                        # 3. Extrair o Número de Cliente
                        cliente = "N/D"
                        linhas = texto.split('\n')
                        for idx, linha in enumerate(linhas):
                            if "Contribuinte" in linha and "Cliente" in linha:
                                if idx + 1 < len(linhas):
                                    valores = linhas[idx+1].split()
                                    if len(valores) >= 2:
                                        cliente = valores[1]
                                break
                        
                        # 4. Guardar a linha da tabela
                        dados.append({
                            "Data da Fatura": data_match.group(1) if data_match else "N/D",
                            "Número de Cliente": cliente,
                            "Número da Fatura": fatura_match.group(1).strip(),
                            "Valor": valor
                        })
            
            if dados:
                df = pd.DataFrame(dados)
                st.success(f"Foram encontradas {len(dados)} faturas!")
                st.dataframe(df, use_container_width=True)
                
                csv = df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button(
                    label="📥 Descarregar para Excel",
                    data=csv,
                    file_name="faturas_resumo.csv",
                    mime="text/csv",
                )
            else:
                st.warning("Não consegui encontrar o formato esperado de fatura nestas páginas.")
