import streamlit as st
import pdfplumber
import pandas as pd
import re

# Configuração da página da App
st.set_page_config(page_title="Extrator de Faturas", layout="centered")
st.title("🧾 Extrator Rápido de Faturas")
st.write("Extrai a Data, Número de Cliente, Número da Fatura e Valor.")

# Área para carregar o ficheiro na app
ficheiro_carregado = st.file_uploader("Arraste o ficheiro PDF aqui", type=["pdf"])

if ficheiro_carregado is not None:
    if st.button("Extrair Dados"):
        with st.spinner("A analisar o PDF..."):
            dados = []
            
            # Padrões de texto (Regex) para encontrar os dados
            padrao_fatura = r"Fatura N\.º\s+(.+)"
            padrao_data = r"Data de Emissão:\s+(\d{2}-\d{2}-\d{4})"
            
            # Lê o PDF carregado
            with pdfplumber.open(ficheiro_carregado) as pdf:
                for pagina in pdf.pages:
                    texto = pagina.extract_text()
                    if not texto:
                        continue
                        
                    # 1. Procurar Fatura e Data
                    fatura_match = re.search(padrao_fatura, texto)
                    data_match = re.search(padrao_data, texto)
                    
                    if fatura_match: # Só processa se for uma página de fatura
                        # 2. Extrair o Valor Total (Procura "Total a pagar" e captura o valor com € a seguir)
                        valor_match = re.search(r"Total a pagar[\s\S]*?([\d.,]+€)", texto)
                        valor = valor_match.group(1).strip() if valor_match else "N/D"

                        # 3. Extrair o Número de Cliente
                        # Nas faturas Moloni, os dados costumam estar numa tabela por baixo das palavras "Contribuinte Cliente"
                        cliente = "N/D"
                        linhas = texto.split('\n')
                        for idx, linha in enumerate(linhas):
                            if "Contribuinte" in linha and "Cliente" in linha:
                                # Apanha a linha seguinte que contém os valores
                                if idx + 1 < len(linhas):
                                    valores = linhas[idx+1].split()
                                    if len(valores) >= 2:
                                        cliente = valores[1] # O Cliente é a 2ª coluna
                                break
                        
                        # Guardar a linha da tabela
                        dados.append({
                            "Data da Fatura": data_match.group(1) if data_match else "N/D",
                            "Número de Cliente": cliente,
                            "Número da Fatura": fatura_match.group(1).strip(),
                            "Valor": valor
                        })
            
            # Mostrar os resultados na App
            if dados:
                df = pd.DataFrame(dados)
                st.success(f"Foram encontradas {len(dados)} faturas!")
                
                # Mostra a tabela no ecrã
                st.dataframe(df, use_container_width=True)
                
                # Cria o botão de download do CSV com o separador corrigido para o Excel PT (sep=';')
                csv = df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button(
                    label="📥 Descarregar para Excel",
                    data=csv,
                    file_name="faturas_resumo.csv",
                    mime="text/csv",
                )
            else:
                st.warning("Não consegui encontrar o formato esperado de fatura nestas páginas.")