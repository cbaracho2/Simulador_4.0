import streamlit as st
import time
import pandas as pd
import numpy as np
from datetime import datetime, date
import seaborn as sns
from openpyxl import Workbook
from st_aggrid import AgGrid, DataReturnMode, GridUpdateMode, GridOptionsBuilder, JsCode
#from tqdm import tqdm
import matplotlib.pyplot as plt
import sqlalchemy   
from scipy import stats
import mysql.connector
import plotly.express as px
from plotly import graph_objects as go
import psycopg2
import warnings
import pickle
import smtplib, ssl
from streamlit.components.v1 import iframe
import pdfkit
#path_wkthmltopdf = 'C://Users//italo//wkhtmltox//bin//wkhtmltopdf.exe'
#config = pdfkit.configuration(wkhtmltopdf=path_wkthmltopdf)    
from jinja2 import Environment, PackageLoader, select_autoescape, FileSystemLoader
from email import encoders
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from deta import Deta
import json
Data_Hoje = pd.to_datetime(date.today(),errors="coerce")
import streamlit.components.v1 as components
st.set_page_config(page_icon="https://7lm.com.br/wp-content/themes/7lm/build/img/icons/assinatura_7lm.png", layout="wide", page_title="GRUPO IMERGE | FERRAMENTA")

def tratar_error_divisor(n, d):
    try:
        result = np.round(n/d,2)
    except:
        result = 0
    return result

def tratar_error_soma(n, d):
    try:
        result = n+d
    except:
        result = 0
    return result

def tratar_error_universal(funcao):
    try:
        result = funcao
    except:
        result = 0
    return result

def conversor_moeda_brasil(my_value):
    a = '{:,.2f}'.format(float(my_value))
    b = a.replace(',','v')
    c = b.replace('.',',')
    return c.replace('v','.')

def form_html(vlr_total, vlr_proposta,txt_box, vlt_tt_otimizado):
    form = f"""
        <!doctype html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://getbootstrap.com/docs/5.2/assets/css/docs.css" rel="stylesheet">
            <title>Bootstrap Example</title>
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/js/bootstrap.bundle.min.js"></script>
        </head>
        <body class="container">
            <div class="row">
                <div class="col">
                    <div class="card shadow-sm p-3 mb-5 bg-body rounded-4" style="width: 20rem; margin-bottom: 15px; border-radius:15px">
                        <div class="card-header text-center">
                            VALOR TOTAL
                        </div>
                    <div class="card-body">
                        <p class="fs-2 text-center">R$ {conversor_moeda_brasil(vlr_total)}</p>
                        <p class="card-text text-center"><small class="text-muted">Valor Otimizado: R$ {conversor_moeda_brasil(vlt_tt_otimizado)}</small></p>
                    </div>
                    </div>
                </div>
                <div class="col">
                    <div class="card shadow-sm p-3 mb-5 bg-body rounded-4" style="width: 20rem; margin-bottom: 15px; border-radius:15px">
                        <div class="card-header text-center">
                            VALOR DA PROPOSTA
                        </div>
                    <div class="card-body">
                        <p class="fs-2 text-center">R$ {conversor_moeda_brasil(vlr_proposta)}</p>
                        <p class="card-text text-center"><small class="text-muted">Gap proposta: R$ {conversor_moeda_brasil(vlr_proposta - vlr_total)}</small></p>
                    </div>
                    </div>
                </div>    
                <div class="col">
                    <div class="card shadow-sm p-3 mb-5 bg-body rounded-4" style="width: 20rem; margin-bottom: 15px; border-radius:15px">
                        <div class="card-header text-center">
                            GAP (%)
                        </div>
                    <div class="card-body">
                        <p class="fs-2 text-center">{(tratar_error_divisor(vlr_proposta, vlr_total))}%</p>
                        <p class="card-text text-center"><small class="text-muted">Gap Otimizado: {(conversor_moeda_brasil((vlr_proposta - vlt_tt_otimizado)))}</small></p>
                    </div>
                    </div>
                </div>      
                <div class="col">
                    <div class="card shadow-sm p-3 mb-5 bg-body rounded-4" style="width: 25rem; margin-bottom: 15px; border-radius:15px">
                        <div class="card-header text-center">
                            STATUS DE APROVAÇÃO
                        </div>
                    <div class="card-body">
                        <p class="fs-2 text-center">{"EM ANÁLISE"}</p>
                        <p class="card-text text-center"><small class="text-muted">{"Resultado prévio da simulação."}</small></p>
                    </div>
                    </div>
                </div>  
            </div>
        </body>
        </html>"""
    return st.markdown(form, unsafe_allow_html=True )          

def OTIMIZAR_PLANO_PGTO(PM, QTDPM, PM_POS, QTDPMPOS, INTPRE, QTDINTPRE, INTPOS, QTDINTPOS, FIN, SUB, FGTS, CH, LAUDO, VGV):
    # Pacote de importação
    import pulp as op
    import pandas as pd
    limite_parcela_pre = PM     # ================= A
    limite_parcela_pre_qtd = QTDPM # ================= B

    limite_parcela_pos = PM_POS     # ================= C
    limite_parcela_pos_qtd = QTDPMPOS # ================= D

    limite_intermediaria_pre = INTPRE # ================= E
    limite_intermediaria_pre_qtd = QTDINTPRE # ================= F

    limite_intermediaria_pos = INTPOS # ================= G
    limite_intermediaria_pos_qtd = QTDINTPOS # ================= H

    limite_fin = FIN # ================= I
    limite_sub = SUB # ================= J
    limite_fgts = FGTS # ================= L
    limite_cheque = CH # ================= M

    limite_pre = VGV * 0.05 # ================= N
    limite_pos = VGV * 0.15 # ================= O
    Garantido = (LAUDO + 10000) - 42000 # ================= P
    vgv = VGV

    # Definir ambiente e direção de otimização
    prob = op.LpProblem("MyOptProblem", op.LpMaximize)

    # Definir variáveis de decisão
    A = op.LpVariable("limite_parcela_pre", lowBound = 0, upBound = None, cat='Continuous')
    B = op.LpVariable("limite_parcela_pre_qtd", lowBound = 0, upBound = None, cat='Integer')

    C = op.LpVariable("limite_parcela_pos", lowBound = 0, upBound = None, cat='Continuous')
    D = op.LpVariable("limite_parcela_pos_qtd", lowBound = 0, upBound = None, cat='Continuous')

    E = op.LpVariable("limite_intermediaria_pre", lowBound = 0, upBound = None, cat='Continuous')
    F = op.LpVariable("limite_intermediaria_pre_qtd", lowBound = 0, upBound = None, cat='Continuous')

    G = op.LpVariable("limite_intermediaria_pos", lowBound = 0, upBound = None, cat='Continuous')
    H = op.LpVariable("limite_intermediaria_pos_qtd", lowBound = 0, upBound = None, cat='Continuous')

    I = op.LpVariable("limite_fin", lowBound = 0, upBound = None, cat='Continuous')
    J = op.LpVariable("limite_sub", lowBound = 0, upBound = None, cat='Continuous')
    L = op.LpVariable("limite_fgts", lowBound = 0, upBound = None, cat='Continuous')
    M = op.LpVariable("limite_cheque", lowBound = 0, upBound = None, cat='Continuous')

    N = op.LpVariable("limite_pre", lowBound = 0, upBound = None, cat='Continuous')
    O = op.LpVariable("limite_pos", lowBound = 0, upBound = None, cat='Continuous')
    P = op.LpVariable("Garantido", lowBound = 0, upBound = None, cat='Continuous')

    # Adicionar função objetiva ao meio ambiente

    prob += A*limite_parcela_pre_qtd+C*limite_parcela_pos_qtd+E*limite_intermediaria_pre_qtd+G*limite_intermediaria_pos_qtd+I+J+L+M, "Objective"

    # Adicionar restrições ao meio ambiente
    prob += A*limite_parcela_pre_qtd+C*limite_parcela_pos_qtd+E*limite_intermediaria_pre_qtd+limite_intermediaria_pos_qtd*H+I+J+L+M >= vgv, "Constraint0"
    prob += A*limite_parcela_pre_qtd + E*limite_parcela_pos_qtd >= limite_pre, "Constraint1"
    prob += C*limite_parcela_pos_qtd + G*limite_intermediaria_pos_qtd <= limite_pos, "Constraint2"
    prob += I == limite_fin,  "Constraint3"
    prob += J == limite_sub,  "Constraint4"
    prob += L == limite_fgts,  "Constraint5"
    prob += M == limite_cheque,  "Constraint6"
    prob += A <= limite_parcela_pre,  "Constraint7"
    prob += C <= limite_parcela_pos,  "Constraint8"
    prob += E <= limite_intermediaria_pre,  "Constraint9"
    prob += G <= limite_intermediaria_pos,  "Constraint10"

    # Resolver o problema (outros solucionadores: prob.solve(SOLVERNAME()))
    prob.solve()
    df_solve = pd.DataFrame()
    lst_solve_1 = []
    lst_solve_2 = []
    
    
    # O status da solução
    print("Status:", op.LpStatus[prob.status])

    # Para exibir as variáveis de decisão ideais
    for variables in prob.variables():
        #print(variables.name, "=", variables.varValue)
        lst_solve_1.append(variables.name)
        lst_solve_2.append(variables.varValue)
        
    df_solve["name"] = lst_solve_1
    df_solve["Value"] = lst_solve_2
    
    # Para exibir o valor ideal da função objetiva
    list = [op.value(prob.objective)]
    #print("Optimal Value of Objective Is = ", op.value(prob.objective)),
    return  df_solve

def card_colorido():
    crd = f"""
            <!doctype html>
            <html lang="en">
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/css/bootstrap.min.css" rel="stylesheet">
                <link href="https://getbootstrap.com/docs/5.2/assets/css/docs.css" rel="stylesheet">
                <title>Bootstrap Example</title>
                <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/js/bootstrap.bundle.min.js"></script>
            </head>
            <body class="p-3 m-0 border-0 bd-example">
                <div class="card" style="width: 35rem; margin-bottom: 20px">
                <div class="card-header text-center">
                    Análise do Resultado
                </div>
                <ul class="list-group list-group-flush">
                    <li class="list-group-item">#1 | Pré Chave: | R$ 42.000,00 | R$ 42.000,00 | 0,00%</li>
                    <li class="list-group-item">#2 | Pós Chave: | R$ 42.000,00 | R$ 42.000,00 | 0,00%</li>
                    <li class="list-group-item">#3 | Garantido: | R$ 42.000,00 | R$ 42.000,00 | 0,00%</li>
                    <li class="list-group-item">#4 | Ch Moradia:| R$ 42.000,00 | R$ 42.000,00 | 0,00%</li>
                    <li class="list-group-item">#5 | Tot_Geral:   | R$ 42.000,00 | R$ 42.000,00 | 0,00%</li>                    
                </ul>
                </div>
            </body>
            </html>"""
    return st.markdown(crd, unsafe_allow_html=True) 

def DEFINIR_STATUS(valor):
    if valor < 0:
        resultado = "Reprovado"
    else:
        resultado = "Aprovado"
    return resultado

def DEFINIR_STATUS_COR(valor):
    if valor < 0:
        resultado = "table-danger"
    else:
        resultado = "table-success"
    return resultado

def DEFINIR_STATUS_COR_CONTRARIO(valor):
    if valor > 0:
        resultado = "table-danger"
    else:
        resultado = "table-success"
    return resultado

def DEFINIR_STATUS_CONTRARIO(valor):
    if valor > 0:
        resultado = "Reprovado"
    else:
        resultado = "Aprovado"
    return resultado

def dataframe_html(lt_pre, lt_pos, lt_gar, pre, pos, gar_, vgv_pp, vgv_, ch):
    verde = "table-success"
    alerta = "table-danger"
    secondary = "table-secondary"

    if sum([lt_pos, pos]) <=0:
        resultado_pos = 0
    else:
        resultado_pos = np.round((pos/vgv_pp)*100,2)
    
    if sum([lt_pre, pre]) <=0:
        resultado = 0
    else:
        resultado = np.round((pre/vgv_pp)*100,2)
    
    html = f"""
            <!doctype html>
            <html lang="en">
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/css/bootstrap.min.css" rel="stylesheet">
                <link href="https://getbootstrap.com/docs/5.2/assets/css/docs.css" rel="stylesheet">
                <title>Bootstrap Example</title>
                <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/js/bootstrap.bundle.min.js"></script>
            </head>
            <div class="card shadow-sm p-3 mb-5 bg-body rounded-4" style="width: 55rem; margin-bottom: 15px; border-radius:15px; height: 295px">
                <table class="table caption-top" style="width: 53rem; margin-top: -19px">
                    <caption>Análise do Resultado | Composição do Plano</caption>
                    <thead>
                        <tr>
                        <th class={secondary} scope="col">#</th>
                        <th class={secondary} scope="col">Métrica:</th>
                        <th class={secondary} scope="col">Limite:</th>
                        <th class={secondary} scope="col">Proposta:</th>
                        <th class={secondary} scope="col">Gap (%):</th>
                        <th class={secondary} scope="col">Gap ($):</th>
                        <th class={secondary} scope="col">Resultado:</th>
                        </tr>
                    </thead>
                    <tbody class="table-group-divider">
                        <tr>
                            <th scope="row">1</th>
                            <td>Pré Chave:</td>
                            <td>R$ {conversor_moeda_brasil(lt_pre)}</td>
                            <td>R$ {conversor_moeda_brasil(pre)}</td>
                            <td>{resultado}%</td>
                            <td>R$ {conversor_moeda_brasil(pre - lt_pre)}</td>
                            <td class={DEFINIR_STATUS_COR(pre - lt_pre)}>{DEFINIR_STATUS(pre - lt_pre)}</td>
                        </tr>
                        <tr>
                            <th scope="row">2</th>
                            <td>Pós Chave:</td>
                            <td>R$ {conversor_moeda_brasil(lt_pos)}</td>
                            <td>R$ {conversor_moeda_brasil(pos)}</td>
                            <td>{resultado_pos}%</td>
                            <td>R$ {conversor_moeda_brasil(pos - lt_pos)}</td>
                            <td class={DEFINIR_STATUS_COR_CONTRARIO(pos - lt_pos)}>{DEFINIR_STATUS_CONTRARIO(pos - lt_pos)}</td>
                        </tr>
                            <th scope="row">3</th>
                            <td>Cheque:</td>
                            <td>R$ {conversor_moeda_brasil(42000)}</td>
                            <td>R$ {conversor_moeda_brasil(ch)}</td>
                            <td>{tratar_error_divisor(ch,42000)}%</td>
                            <td>R$ {conversor_moeda_brasil(ch - 42000)}</td>
                            <td class={DEFINIR_STATUS_COR(ch - 42000)}>{DEFINIR_STATUS(ch - 42000)}</td>                       
                        <tr>
                            <th scope="row">4</th>
                            <td>Garantido:</td>
                            <td>R$ {conversor_moeda_brasil(lt_gar)}</td>
                            <td>R$ {conversor_moeda_brasil(gar_)}</td>
                            <td>{tratar_error_divisor(gar_,lt_gar)}%</td>
                            <td>R$ {conversor_moeda_brasil(gar_- lt_gar)}</td>
                            <td class={DEFINIR_STATUS_COR(gar_ - lt_gar)}>{DEFINIR_STATUS(gar_ - lt_gar)}</td>
                        </tr>
                        <tr>
                            <th class={secondary} scope="row">5</th>
                            <td class={secondary}>Total Geral:</td>
                            <td class={secondary}>R$ {conversor_moeda_brasil(vgv_)}</td>
                            <td class={secondary}>R$ {conversor_moeda_brasil(vgv_pp)}</td>
                            <td class={secondary}>{((tratar_error_divisor((vgv_pp),(vgv_))))}%</td>
                            <td class={secondary}>R$ {conversor_moeda_brasil(vgv_pp- vgv_)}</td>
                            <td class={DEFINIR_STATUS_COR(vgv_pp - vgv_)}>{DEFINIR_STATUS(vgv_pp - vgv_)}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            </html>"""
    return st.markdown(html, unsafe_allow_html=True) 

def dataframe_html_detalhado(pm_pre, qtd_pm_pre, pm_pos, qtd_pm_pos, fin, fgts, sub, ch, int_pre_1, qt_int_pre_1, int_pre_2, qt_int_pre_2, int_pos_1, qt_int_pos_1, 
                             int_pos_2, qt_int_pos_2,pmovel, qt_pmovel, sinal, qt_sinal, ot_pm_pre, ot_pm_pos, ot_int_pre, ot_int_pos, tt_otm, ot_qtd_mensais_pre, ot_qtd_mensais_pos):
    secondary = "table-secondary"
    primary = "table-primary"
    info  = "table-info"
    
    df_html = f""" 
        <!doctype html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://getbootstrap.com/docs/5.2/assets/css/docs.css" rel="stylesheet">
            <title>Bootstrap Example</title>
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/js/bootstrap.bundle.min.js"></script>
        </head>
        <body class="p-3 m-0 border-0 bd-example">
        <div class="card shadow-sm p-3 mb-5 bg-body rounded-4" style="width: 90rem; margin-bottom: 15px; border-radius:15px; height: 670px">
            <table class="table caption-top">
            <caption>Análise do Resultado | Plano estratificado</caption>
            <thead>
                <tr>
                <th class={primary} scope="col">#</th>
                <th class={primary} scope="col">Série</th>
                <th class={primary} scope="col">Parcela</th>
                <th class={primary} scope="col">Quantidade</th>
                <th class={primary} scope="col">Subtotal</th>
                <th class={info} scope="col">Parcela-Otimiz</th>
                <th class={info} scope="col">Valor-Otimiz</th>
                <th class={info} scope="col">Subtotal-Otimiz</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                <th scope="row">1</th>
                <td>Entrada</td>
                <td>R$ {conversor_moeda_brasil(sinal)}</td>
                <td>{int(qt_sinal)}</td>
                <td>R$ {conversor_moeda_brasil(sinal * int(qt_sinal))}</td>
                <td class="text-bg-light">R$ 0,00</td>
                <td class="text-bg-light">0</td>
                <td class="text-bg-light">R$ 0,00</td>
                </tr>
                <tr>
                <th scope="row">2</th>
                <td>Mensais Pré</td>
                <td>R$ {conversor_moeda_brasil(pm_pre)}</td>
                <td>{int(qtd_pm_pre)}</td>
                <td>R$ {conversor_moeda_brasil(pm_pre * int(qtd_pm_pre))}</td>
                <td class="text-bg-light">R$ {conversor_moeda_brasil(ot_pm_pre)}</td>
                <td class="text-bg-light">{int(ot_qtd_mensais_pre)}</td>
                <td class="text-bg-light">R$ {conversor_moeda_brasil(ot_pm_pre * int(ot_qtd_mensais_pre))}</td>
                </tr>
                <tr>
                <th scope="row">3</th>
                <td>Mensais Pós</td>
                <td>R$ {conversor_moeda_brasil(pm_pos)}</td>
                <td>{int(qtd_pm_pos)}</td>
                <td>R$ {conversor_moeda_brasil(pm_pos * int(qtd_pm_pos))}</td>
                <td class="text-bg-light">R$ {conversor_moeda_brasil(ot_pm_pos)}</td>
                <td class="text-bg-light">{int(ot_qtd_mensais_pos)}</td>
                <td class="text-bg-light">R$ {conversor_moeda_brasil(ot_pm_pos * int(ot_qtd_mensais_pos))}</td>
                </tr>
                <th scope="row">4</th>
                <td>Interm Pré 1</td>
                <td>R$ {conversor_moeda_brasil(int_pre_1)}</td>
                <td>{int(qt_int_pre_1)}</td>
                <td>R$ {conversor_moeda_brasil(int_pre_1 * int(qt_int_pre_1))}</td>
                <td class="text-bg-light">R$ {conversor_moeda_brasil(ot_int_pre)}</td>
                <td class="text-bg-light">2</td>
                <td class="text-bg-light">R$ {conversor_moeda_brasil(ot_int_pre * int(2))}</td>
                </tr>
                <th scope="row">5</th>
                <td>Interm Pré 2</td>
                <td>R$ {conversor_moeda_brasil(int_pre_2)}</td>
                <td>{int(qt_int_pre_2)}</td>
                <td>R$ {conversor_moeda_brasil(int_pre_2 * int(qt_int_pre_2))}</td>
                <td class="text-bg-light">R$ 0,00</td>
                <td class="text-bg-light">0</td>
                <td class="text-bg-light">R$ 0,00</td>
                </tr>
                <th scope="row">6</th>
                <td>Interm Pós 1</td>
                <td>R$ {conversor_moeda_brasil(int_pos_1)}</td>
                <td>{int(qt_int_pos_1)}</td>
                <td>R$ {conversor_moeda_brasil(int_pos_1 * int(qt_int_pos_1))}</td>
                <td class="text-bg-light">R$ {conversor_moeda_brasil(ot_int_pos)}</td>
                <td class="text-bg-light">2</td>
                <td class="text-bg-light">R$ {conversor_moeda_brasil(ot_int_pos * int(2))}</td>
                </tr>
                <th scope="row">7</th>
                <td>Interm Pós 2</td>
                <td>R$ {conversor_moeda_brasil(int_pos_2)}</td>
                <td>{int(qt_int_pos_2)}</td>
                <td>R$ {conversor_moeda_brasil(int_pos_2 * int(qt_int_pos_2))}</td>
                <td class="text-bg-light">R$ 0,00</td>
                <td class="text-bg-light">0</td>
                <td class="text-bg-light">R$ 0,00</td>
                </tr>
                <th scope="row">8</th>
                <td>Parcela Móvel</td>
                <td>R$ {conversor_moeda_brasil(pmovel)}</td>
                <td>{int(qt_pmovel)}</td>
                <td>R$ {conversor_moeda_brasil(pmovel * int(qt_pmovel))}</td>
                <td class="text-bg-light">R$ 0,00</td>
                <td class="text-bg-light">0</td>
                <td class="text-bg-light">R$ 0,00</td>
                </tr>
                <th scope="row">9</th>
                <td>Financiamento</td>
                <td>R$ {conversor_moeda_brasil(fin)}</td>
                <td>1</td>
                <td>R$ {conversor_moeda_brasil(fin)}</td>
                <td class="text-bg-light">R$ {conversor_moeda_brasil(fin)}</td>
                <td class="text-bg-light">1</td>
                <td class="text-bg-light">R$ {conversor_moeda_brasil(fin)}</td>
                </tr>
                <th scope="row">10</th>
                <td>Subsídio</td>
                <td>R$ {conversor_moeda_brasil(sub)}</td>
                <td>1</td>
                <td>R$ {conversor_moeda_brasil(sub)}</td>
                <td class="text-bg-light">R$ {conversor_moeda_brasil(sub)}</td>
                <td class="text-bg-light">1</td>
                <td class="text-bg-light">R$ {conversor_moeda_brasil(sub)}</td>
                </tr>
                <th scope="row">11</th>
                <td>FGTS</td>
                <td>R$ {conversor_moeda_brasil(fgts)}</td>
                <td>1</td>
                <td>R$ {conversor_moeda_brasil(fgts)}</td>
                <td  class="text-bg-light">R$ {conversor_moeda_brasil(fgts)}</td>
                <td class="text-bg-light">1</td>
                <td class="text-bg-light">R$ {conversor_moeda_brasil(fgts)}</td>
                </tr>
                <th scope="row">12</th>
                <td>Ch_Moradia</td>
                <td>R$ {conversor_moeda_brasil(ch)}</td>
                <td>1</td>
                <td>R$ {conversor_moeda_brasil(ch)}</td>
                <td class="text-bg-light">R$ {conversor_moeda_brasil(ch)}</td>
                <td class="text-bg-light">1</td>
                <td class="text-bg-light">R$ {conversor_moeda_brasil(ch)}</td>
                </tr>
                <th class={secondary} scope="row">13</th>
                <td class={secondary} >Total Geral</td>
                <td class={secondary} >-</td>
                <td class={secondary} >-</td>
                <td class={secondary} >R$ {conversor_moeda_brasil(ch+fin+sub+fgts+sinal*qt_sinal+pm_pre*qtd_pm_pre+pm_pos*qtd_pm_pos+int_pre_1*qt_int_pre_1+int_pre_2*qt_int_pre_2 +  int_pos_1*qt_int_pos_1 + int_pos_2*qt_int_pre_2 +pmovel*qt_pmovel)}</td>
                <td class={secondary} >-</td>
                <td class={secondary} >-</td>
                <td class={secondary} >R$ {conversor_moeda_brasil(tt_otm)}</td>
                </tr>
            </tbody>
            </table>
        </div>            
        </body>
        </html>"""    
    return st.markdown(df_html, unsafe_allow_html=True) 

            #<caption>#1 O limite Pré é o valor MÁX de parcelamento nessa fase</caption>
            #<caption>#1 O limite Pós é o valor MÁX de parcelamento nessa fase</caption>
            #<caption>#1 O limite Gar é o valor MÍN (FIN + FGTS + FIN + SINAL)</caption>


def grid_dataframe_top(df, tamanho):
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(groupable=True, enableValue=True, enableRowGroup=True,aggFunc="sum",editable=True)
    gb.update_mode=GridUpdateMode.MANUAL
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    gb.configure_side_bar()
    gridoptions = gb.build()
    response = AgGrid(
        df,
        height=tamanho,
        gridOptions=gridoptions,
        enable_enterprise_modules=True,
        header_checkbox_selection_filtered_only=True,
        use_checkbox=True, theme="blue")
    return response

Base = pd.read_excel("Base_Preços.xlsx")
c1, c2 = st.columns((1,10))
c1.image("logo7lm.png",use_column_width=True,caption="Simulador" )
c2.title("# SIMULADOR | VENDAS | CREDITO | CAIXA")

col1, col2, col3, col4, col5, col6 = st.columns((3,3,3,3,3,3)) 


lst_emp = list(Base["EMP"].unique()) 
EMP = col1.selectbox("EMPREENDIMENTO", options=lst_emp)
lst_bloco = list(Base.loc[Base["EMP"].isin([EMP])]["BLOCO"].unique())
BLOCO = col2.selectbox("BLOCO", options=lst_bloco)
lst_unid = list(Base.loc[(Base["EMP"]==EMP) & (Base["BLOCO"]==BLOCO)]["UNIDADE"].unique())
APTO = col3.selectbox("UNIDADE", options=lst_unid)
VALOR_TABELA = list(Base.loc[(Base["EMP"]==EMP) & (Base["BLOCO"]==BLOCO) & (Base["UNIDADE"]==APTO)]["VALOR DE VENDA"].unique())[0]
VALOR_LAUDO = list(Base.loc[(Base["EMP"]==EMP) & (Base["BLOCO"]==BLOCO) & (Base["UNIDADE"]==APTO)]["VALOR DO LAUDO"].unique())[0]

cx=st.container()



with st.form(key="7lm"):
    c1, c2, c3, c4, c5, c6  = st.columns((2,2,2,2,2,2)) 
    NOME = c1.text_input("NOME_DO_CLIENTE")
    RENDA_1 = c2.number_input("RENDA 1ª PROPONENTE")
    RENDA_2 = c3.number_input("RENDA 2ª PROPONENTE")


    RENDA_FIADOR_1 = c1.number_input("RENDA_FIADOR_01")
    RENDA_FIADOR_2 = c2.number_input("RENDA_FIADOR_02")
    SCORE_1 = c3.number_input("SCORE 1ª PROPONENTE")
    SCORE_2 = c4.number_input("SCORE 2ª PROPONENTE")
    SCORE_3 = c5.number_input("SCORE 1ª FIADOR")
    SCORE_4 = c6.number_input("SCORE 2ª FIADOR")
    bt1 = st.form_submit_button("ATUALIZAR")

resultado_caixinhas = st.container()
with resultado_caixinhas:
    status = "Em Análise"
    
    
    
 
with st.form(key="8lm"):
    c1, c2, c3, c4, c5  = st.columns((2,1,2,2,2)) 
    SINAL = c1.number_input("Valor do Sinal")
    QTD_SINAL = c2.number_input("Quant", format=   "%.0f")
    TOTAL_SINAL = c3.number_input("Total", value= SINAL*QTD_SINAL ,  disabled=True)
    DATA_SINAL = c4.text_input("Data")
    ST_1 = c5.text_input(f"Análise Otimização 1",disabled=True,value=status)

    MENSAIS = c1.number_input("Valor das Mensais Pré")
    QTD_MENSAIS = c2.number_input("Quant Mensais Pré", format=   "%.0f")
    TOTAL_MENSAIS = c3.number_input("Total Mensais Pré",value= MENSAIS*QTD_MENSAIS ,  disabled=True)
    DATA_MENSAIS = c4.text_input("Data Mensais Pré")
    ST_2 = c5.text_input(f"Análise Otimização 2",disabled=True,value=status)

    MENSAIS_POS = c1.number_input("Valor das Mensais Pós")
    QTD_MENSAIS_POS = c2.number_input("Quant Mensais Pós", format=   "%.0f")
    TOTAL_MENSAIS_POS = c3.number_input("Total Mensais Pós",value= MENSAIS_POS*QTD_MENSAIS_POS, disabled=True)
    DATA_MENSAIS_POS = c4.text_input("Data Mensais Pós")
    ST_3 = c5.text_input(f"Análise Otimização 3",disabled=True,value=status)
    
    INTER_1 = c1.number_input("Valor da Inter_1 Pré Chave")
    QTD_INTER_1 = c2.number_input("Quant Inter_1", format=   "%.0f")
    TOTAL_INTER_1 = c3.number_input("Total Inter_1",value= INTER_1*QTD_INTER_1, disabled=True)
    DATA_INTER_1 = c4.text_input("Data Mensais Inter_1")    
    ST_4 = c5.text_input(f"Análise Otimização 4",disabled=True,value=status)

    INTER_2 = c1.number_input("Valor da Inter_2 Pré Chave")
    QTD_INTER_2 = c2.number_input("Quant Inter_2", format=   "%.0f")
    TOTAL_INTER_2 = c3.number_input("Total Inter_2",value= INTER_2*QTD_INTER_2, disabled=True)
    DATA_INTER_2 = c4.text_input("Data Mensais Inter_2")  
    ST_5 = c5.text_input(f"Análise Otimização 5",disabled=True,value=status)

    INTER_3 = c1.number_input("Valor da Inter_3 Pós Chave")
    QTD_INTER_3 = c2.number_input("Quant Inter_3", format=   "%.0f")
    TOTAL_INTER_3 = c3.number_input("Total Inter_3",value= INTER_3*QTD_INTER_3, disabled=True)
    DATA_INTER_3 = c4.text_input("Data Mensais Inter_3")  
    ST_6 = c5.text_input(f"Análise Otimização 6",disabled=True,value=status)
    
    INTER_4 = c1.number_input("Valor da Inter_4 Pós Chave")
    QTD_INTER_4 = c2.number_input("Quant Inter_4", format=   "%.0f")
    TOTAL_INTER_4 = c3.number_input("Total Inter_4",value= INTER_4*QTD_INTER_4, disabled=True)
    DATA_INTER_4 = c4.text_input("Data Mensais Inter_4")  
    ST_7 = c5.text_input(f"Análise Otimização 7",disabled=True,value=status)
    
    INTER_5 = c1.number_input("Valor da Inter_5 Pós Chave")
    QTD_INTER_5 = c2.number_input("Quant Inter_5", format=   "%.0f")
    TOTAL_INTER_5 = c3.number_input("Total Inter_5",value= INTER_5*QTD_INTER_5, disabled=True)
    DATA_INTER_5 = c4.text_input("Data Mensais Inter_5")
    ST_8 = c5.text_input(f"Análise Otimização 8",disabled=True,value=status)
    
    st.subheader("VALORES DO FINANCIAMENTO")
    c1, c2, c3, c4, c5  = st.columns((2,1,2,2,2)) 
    CHEQUE_MORADIA = c1.number_input("Cheque_Moradia")
    FGTS = c2.number_input("FGTS")
    SUBSÍDIO = c3.number_input("Subísidio")
    FINANCIAMENTO = c4.number_input("Financiamento")
    VALOR_PROPOSTA = (SINAL * QTD_SINAL) + (MENSAIS*QTD_MENSAIS) + (MENSAIS_POS * QTD_MENSAIS_POS) + (INTER_1*QTD_INTER_1)+ (INTER_2*QTD_INTER_2) + (INTER_3*QTD_INTER_3)+ (INTER_4*QTD_INTER_4)+ (INTER_5*QTD_INTER_5) + CHEQUE_MORADIA + SUBSÍDIO + FGTS + FINANCIAMENTO
    DIFERENCA =  VALOR_TABELA - VALOR_PROPOSTA
    PRE = (MENSAIS*QTD_MENSAIS) + (INTER_2*QTD_INTER_2) + (INTER_1*QTD_INTER_1)
    POS = (MENSAIS_POS*QTD_MENSAIS_POS) + (INTER_3*QTD_INTER_3) + (INTER_4*QTD_INTER_4) + (INTER_5*QTD_INTER_5)
    GAR = (SINAL * QTD_SINAL) + SUBSÍDIO + FGTS + FINANCIAMENTO
    
    
    def VALOR_DO_GARANTIDO(EMP, laudo_):
        if EMP == "VILA DO CERRADO" or EMP == "VILA DAS HORTENCIAS":
            GAR = 120000.00
        else:
            GAR = laudo_ - 42000 + 10000
        return GAR
    
    #limite_Pre_Pos_Garantido
    lim_pre = VALOR_PROPOSTA * 0.0700 
    lim_pos = VALOR_PROPOSTA * 0.0469
    lim_gar = VALOR_DO_GARANTIDO(EMP, VALOR_LAUDO)   
    
    # AVALIAR O POTENCIAL DO CLIENTE DE ACORDO COM SUA RENDA E SCORE ====================================================================================================
    
    DT_ENTREGA = {"VILA DO CERRADO":"2024-08-01","VILA DO SOL":"2023-05-01","VILA DAS AGUAS":"2022-07-01","VILA AZALEIA":"2023-05-01", "VILA DAS ORQUÍDEAS":"2023-06-01","VILA DAS TULIPAS":"2023-12-01","VILA DAS HORTENCIAS":"2024-12-01"}
    DT_ENTREGA1 = {"AGL28":"2024-08-01","AGL23":"2023-05-01","AGL25":"2022-07-01","AGL27":"2023-05-01", "FSA005":"2023-06-01","FSA006":"2023-12-01","FSA007":"2024-09-01"}

    
    def POTENCIAL_INTERM(RENDA, DT_HOJE, DT_PGTO):
        dt_01 = pd.to_datetime(DT_HOJE, errors="coerce")
        dt_02 = pd.to_datetime(DT_PGTO, errors="coerce")
        T_DIAS = int(((dt_02-dt_01).days)/30.41)
        PARC_COMP = tratar_error_universal(RENDA * 1.33)
        RESULTADO = tratar_error_universal((PARC_COMP * T_DIAS)/12)
        return np.round(RESULTADO*0.25,2)
    

    COEF_PRE = 0.225
    COEF_POS = 0.125
    OT_QTD_MENSAIS_PRE = int((pd.to_datetime(DT_ENTREGA[EMP], errors="coerce") - pd.to_datetime(datetime.today(), errors="coerce")).days/30.25)
    OT_QTD_MENSAIS_POS = tratar_error_universal(int(60 - OT_QTD_MENSAIS_PRE)) 
    RENDA_TOTAL_ = tratar_error_soma(RENDA_1 , RENDA_2)
    OT_INTER_ = POTENCIAL_INTERM(RENDA_TOTAL_, datetime.today(), DT_ENTREGA[EMP])
    OT_PM_PRE = tratar_error_universal(RENDA_TOTAL_* COEF_PRE)
    OT_PM_POS = tratar_error_universal(RENDA_TOTAL_* COEF_POS)
    
    OTIMIZADOR = OTIMIZAR_PLANO_PGTO(OT_PM_PRE, OT_QTD_MENSAIS_PRE, OT_PM_POS, OT_QTD_MENSAIS_POS, OT_INTER_, 2, OT_INTER_, 2, FINANCIAMENTO, SUBSÍDIO, FGTS, CHEQUE_MORADIA, VALOR_LAUDO, VALOR_TABELA  )
    #st.write(OTIMIZADOR)
    # =========================================================================================================================================================
    def Otimizador_resultado(rend_001, rend_002, fin):
        if (rend_001 + rend_002) > 0 or (fin) > 0:
            limite_parcela_pre =  list(OTIMIZADOR.loc[OTIMIZADOR["name"]=="limite_parcela_pre"]["Value"])[0]
            limite_parcela_pos =  list(OTIMIZADOR.loc[OTIMIZADOR["name"]=="limite_parcela_pos"]["Value"])[0]
            limite_intermediaria_pre =  list(OTIMIZADOR.loc[OTIMIZADOR["name"]=="limite_intermediaria_pre"]["Value"])[0]
            limite_intermediaria_pos =  list(OTIMIZADOR.loc[OTIMIZADOR["name"]=="limite_intermediaria_pos"]["Value"])[0]
        else:
            limite_parcela_pre =  0
            limite_parcela_pos =  0
            limite_intermediaria_pre =  0
            limite_intermediaria_pos =  0
        return limite_parcela_pre, limite_parcela_pos, limite_intermediaria_pre, limite_intermediaria_pos
    
    limite_parcela_pre =  Otimizador_resultado(RENDA_1, RENDA_2, FINANCIAMENTO)[0]
    limite_parcela_pos =  Otimizador_resultado(RENDA_1, RENDA_2, FINANCIAMENTO)[1]
    limite_intermediaria_pre =  Otimizador_resultado(RENDA_1, RENDA_2, FINANCIAMENTO)[2]
    limite_intermediaria_pos =  Otimizador_resultado(RENDA_1, RENDA_2, FINANCIAMENTO)[3]

    st.subheader("RESULTADO DA ANÁLISE")
    
    c1, c2, c3  = st.columns((3,4,4,)) 
    RESULTADO = pd.DataFrame()
    RESULTADO["STATUS"] = ["Pré Chave", "Pós Chave", "Garantido", "Valor Total"]
    RESULTADO["TABELA"] = [0,0,0,VALOR_TABELA]
    RESULTADO["PROPOSTA"] = [0,0,0,VALOR_PROPOSTA]
    RESULTADO["%"] = [0,0,0,0]
    
    RESULTADO_DETALHADO_OT = pd.DataFrame()
    RESULTADO_DETALHADO_OT["STATUS"] = ["SINAL","MENSAL_PRE","MENSAL_POS", "INTER_1","INTER_2","INTER_3","INTER_4","INTER_5",
                                     "CHEQUE","FGTS","SUBSÍDIO","FINANCIAMENTO"]
    RESULTADO_DETALHADO_OT["VALOR_OTIMIZADO"] = [0,limite_parcela_pre,limite_parcela_pos,limite_intermediaria_pre,limite_intermediaria_pos,0,0,0,CHEQUE_MORADIA,FGTS,SUBSÍDIO,FINANCIAMENTO] 
    RESULTADO_DETALHADO_OT["QUANT_OTIMIZADA"] = [0,OT_QTD_MENSAIS_PRE,OT_QTD_MENSAIS_POS,2,2,0,0,0,1,1,1,1] 
    RESULTADO_DETALHADO_OT["VALOR_OTIM"] = RESULTADO_DETALHADO_OT["VALOR_OTIMIZADO"] * RESULTADO_DETALHADO_OT["QUANT_OTIMIZADA"] 
    RESULTADO_DETALHADO_OT["%"] = np.round(RESULTADO_DETALHADO_OT["VALOR_OTIM"] / RESULTADO_DETALHADO_OT["VALOR_OTIM"].sum(), 2)
       
    RESULTADO_DETALHADO = pd.DataFrame()
    RESULTADO_DETALHADO["STATUS"] = ["SINAL","MENSAL_PRE","MENSAL_POS", "INTER_1","INTER_2","INTER_3","INTER_4","INTER_5",
                                     "CHEQUE","FGTS","SUBSÍDIO","FINANCIAMENTO"]
    RESULTADO_DETALHADO["VALOR"] = [0,0,0,0,0,0,0,0,0,0,0,0] 
    RESULTADO_DETALHADO["QUANTIDADE"] = [0,0,0,0,0,0,0,0,0,0,0,0] 
    RESULTADO_DETALHADO["TOTAL"] = [0,0,0,0,0,0,0,0,0,0,0,0] 
    RESULTADO_DETALHADO["%"] = [0,0,0,0,0,0,0,0,0,0,0,0] 
    
   
    with c1:
        doc0 = dataframe_html(lim_pre, lim_pos, lim_gar, PRE, POS, GAR, VALOR_PROPOSTA, VALOR_TABELA, CHEQUE_MORADIA)
        dataframe_html_detalhado(MENSAIS, QTD_MENSAIS, MENSAIS_POS, QTD_MENSAIS_POS, FINANCIAMENTO, FGTS, SUBSÍDIO, CHEQUE_MORADIA, INTER_1, QTD_INTER_1, INTER_2, QTD_INTER_2,
                                 INTER_3, QTD_INTER_3, INTER_4, QTD_INTER_4, INTER_5, QTD_INTER_5, SINAL, QTD_SINAL, limite_parcela_pre, limite_parcela_pos, limite_intermediaria_pre,
                                 limite_intermediaria_pos, RESULTADO_DETALHADO_OT["VALOR_OTIM"].sum(), OT_QTD_MENSAIS_PRE, OT_QTD_MENSAIS_POS)

    bt2 = st.form_submit_button("ATUALIZAR PLANO DE PGTO")
 
with st.expander("FILA DE APROVAÇÃO::"):
    fila_cx = st.container()        
   
with cx:
    form_html(VALOR_TABELA, VALOR_PROPOSTA, DIFERENCA, RESULTADO_DETALHADO_OT["VALOR_OTIM"].sum())
    
COLUNA_001 = ["NOME", "RENDA_1","MENSAIS", "QTD_MENSAIS", "MENSAIS_POS", "QTD_MENSAIS_POS", "FINANCIAMENTO", "FGTS", "SUBSÍDIO", "CHEQUE_MORADIA", "INTER_1", 'QTD_INTER_1', 'INTER_2', 'QTD_INTER_2',
                                 'INTER_3', 'QTD_INTER_3', 'INTER_4', 'QTD_INTER_4', 'INTER_5', 'QTD_INTER_5', 'SINAL', 'QTD_SINAL', 'limite_parcela_pre', 'limite_parcela_pos', 'limite_intermediaria_pre',
                                 'limite_intermediaria_pos', "VALOR_OTIM", 'OT_QTD_MENSAIS_PRE', 'OT_QTD_MENSAIS_POS', "VALOR_TABELA" , "VALOR_PROPOSTA", "DIFERENCA", "EMP", "BLOCO", "APTO", "FILA_CRÉDITO"]

COLUNA_002 = ["key","NOME", "RENDA_1","MENSAIS", "QTD_MENSAIS", "MENSAIS_POS", "QTD_MENSAIS_POS", "FINANCIAMENTO", "FGTS", "SUBSÍDIO", "CHEQUE_MORADIA", "INTER_1", 'QTD_INTER_1', 'INTER_2', 'QTD_INTER_2',
                                 'INTER_3', 'QTD_INTER_3', 'INTER_4', 'QTD_INTER_4', 'INTER_5', 'QTD_INTER_5', 'SINAL', 'QTD_SINAL', 'limite_parcela_pre', 'limite_parcela_pos', 'limite_intermediaria_pre',
                                 'limite_intermediaria_pos', "VALOR_OTIM", 'OT_QTD_MENSAIS_PRE', 'OT_QTD_MENSAIS_POS',"VALOR_TABELA" , "VALOR_PROPOSTA", "DIFERENCA", "EMP", "BLOCO", "APTO", "FILA_CRÉDITO"]


COLUNA_VALUE = [NOME, conversor_moeda_brasil(RENDA_1), MENSAIS, QTD_MENSAIS, MENSAIS_POS, QTD_MENSAIS_POS, FINANCIAMENTO, FGTS, SUBSÍDIO, CHEQUE_MORADIA, INTER_1, QTD_INTER_1, INTER_2, QTD_INTER_2,
                                 INTER_3, QTD_INTER_3, INTER_4, QTD_INTER_4, INTER_5, QTD_INTER_5, SINAL, QTD_SINAL, limite_parcela_pre, limite_parcela_pos, limite_intermediaria_pre,
                                 limite_intermediaria_pos, RESULTADO_DETALHADO_OT["VALOR_OTIM"].sum(), OT_QTD_MENSAIS_PRE, OT_QTD_MENSAIS_POS,conversor_moeda_brasil(VALOR_TABELA), conversor_moeda_brasil(VALOR_PROPOSTA), conversor_moeda_brasil(DIFERENCA), EMP, BLOCO, APTO, "⚠️ Em Análise"]


df_envio_bd = pd.DataFrame(columns=COLUNA_001, index=range(0,1))
df_envio_bd.iloc[0,:] = COLUNA_VALUE

# INFORMAÇÕES DO BANCO DE DADOS ======================================================
ID_BD = "l5s23"
Key_name = "l5s23"
Key = "l5s23"
token = "e03i802t_V7vG8SVvbDr4adaAR7jJWMLYaSAuMtQ7"
# Banco de Dados Principal ======================================================
deta = Deta(token)
db = deta.Base(Key)


def salvar_bd(df, bd):
    df1 = df.astype(str)
    dic_emp = json.loads(json.dumps(list(df1.T.to_dict().values())))
    n=0
    pbar = tqdm(total = len(dic_emp), position=0, leave = True)
    for i in range(0,len(dic_emp)):
        pbar.update()
        bd.put(dic_emp[n])
        n+=1
    return print("Script Finalizado")



def baixa_bd(Banco_Dados, COL):
    res = Banco_Dados.fetch()
    all_items = res.items
    while res.last:
        res = Banco_Dados.fetch(last=res.last)
        all_items += res.items
    banco_de_dados = pd.DataFrame([all_items][0])
    banco_de_dados = banco_de_dados.loc[:, COL]
    return banco_de_dados

def delete_user(key):
    db.delete(key)
    return st.success("Dados Deletado")

def get_user(key):
    user = db.get(key)
    return user

def ATUALIZAR_BANCO_DADOS_PANDAS(Coluna, value, key):
    df1 = get_user(key)
    df1[Coluna] = value
    user = db.put(df1, key)
    return user
 
 
 
 
with fila_cx:
    try:
        a=baixa_bd(db, COLUNA_002)
        col__ =["key","FILA_CRÉDITO","NOME", "RENDA_1","EMP","BLOCO","APTO","VALOR_TABELA","VALOR_PROPOSTA", "DIFERENCA"]
        grid_dataframe_top(a[col__], 200)
    except:
        pass    
 
 #C:\Users\italo\wkhtmltox\bin
path_wkthmltopdf = 'C://Users//italo//wkhtmltox//bin//wkhtmltopdf.exe'
config = pdfkit.configuration(wkhtmltopdf=path_wkthmltopdf)    
    
c1, c2, c3, c4 = st.columns((2, 2, 2, 10))
with c1:
    with st.expander("ID | FILA"):
        bt_0001 = st.button("ENVIAR SIMULAÇÃO")
    if bt_0001:
        salvar_bd(df_envio_bd, db)
        env = Environment(loader=FileSystemLoader("."), autoescape=select_autoescape())
        template = env.get_template("relatorio.html")
        html = template.render(Emp=EMP,date=date.today().strftime("%B %d, %Y"),)
        pdf = pdfkit.from_string(html,configuration=config)
        st.balloons()
        st.success("🎉 Liberação enviada com sucesso!")
        st.download_button("⬇️ Download PDF",data=pdf,file_name="Liberacao.pdf",mime="application/octet-stream")
with c2:
    with st.expander("ID | BUSCA"):
        PROC = st.text_input("ID_SIMULAÇÃO")      
        bt_0002 = st.button("BUSCAR SIMULAÇÃO")
with c3:
    with st.expander("ID | DELETE"):
        DEL = st.text_input("ID SIMULAÇÃO")
        try:  
            delete_user(DEL)
        except:
            pass
        bt_0003 = st.button("DELETAR SIMULAÇÃO")  




def enviar_email(email1, email2):
    import smtplib  
    senha="eqanaygxivacwkgt"
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login("solicitarliberacaodaproposta@gmail.com", senha)
    server.sendmail(email1, email2, "ola")
    

    server.quit()
    return st.write("Email Enviado")







   
    

