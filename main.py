import json
import re
import time
import hmac
import hashlib
import requests
import threading
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivy.uix.screenmanager import NoTransition  # 🛠️ CORREÇÃO AQUI: Importado do Kivy nativo
from kivymd.uix.snackbar import MDSnackbar
from kivymd.uix.label import MDLabel
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.utils import platform

# Ajusta o tamanho da janela para simular um celular durante o desenvolvimento no PC
Window.size = (360, 640)

# 🔐 CREDENCIAIS DO SEU PROJETO BURGOS-30900
WEB_API_KEY = "AIzaSyBQovzONkQ2aQ7vY99mysR9sZiYrvUb7KI"
FIREBASE_URL = "https://burgos-30900.firebaseio.com/"

# 🔑 CREDENCIAIS DA SUA BINANCE
BINANCE_API_KEY = "hxmLLULmp2Z4WGH2aRab3bCyQIHd1ZWdUk4zkK9dhJcOSNOYbGDUIJQNP7WJuxvq"  
BINANCE_SECRET_KEY = "vr5mZ5ilyNF6JfhYoCkzaQeDbuHeyNirmN7nF07RxESti0JZFSXVs2hzPr5IUGiO"
BINANCE_BASE_URL = "https://api.binance.com"

# URLs oficiais do Firebase Authentication
AUTH_REGISTER_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={WEB_API_KEY}"
AUTH_LOGIN_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={WEB_API_KEY}"
AUTH_RESET_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={WEB_API_KEY}"

# Variáveis globais para armazenar as classes nativas sem dar erro de linting no VS Code
PythonActivity = None
AdRequest = None
RewardedAd = None
RecompensaListener = None
RewardedCallback = None

# 🤖 CONFIGURAÇÃO E IMPORTS DO ADMOB NATIVO DENTRO DE STRING (ISOLA COMPLETAMENTE DO PYLANCE)
if platform == "android":
    try:
        exec("""
from jnius import autoclass, PythonJavaClass, java_method

global PythonActivity, AdRequest, RewardedAd, RecompensaListener, RewardedCallback

PythonActivity = autoclass('org.kivy.android.PythonActivity')
AdRequest = autoclass('com.google.android.gms.ads.AdRequest')
RewardedAd = autoclass('com.google.android.gms.ads.rewarded.RewardedAd')

class RecompensaListener(PythonJavaClass):
    __javainterfaces__ = ['com/google/android/gms/ads/rewarded/OnUserEarnedRewardListener']
    __javacontext__ = 'app'

    def __init__(self, callback):
        super(RecompensaListener, self).__init__()
        self.callback = callback

    @java_method('(Lcom/google/android/gms/ads/rewarded/RewardItem;)V')
    def onUserEarnedReward(self, rewardItem):
        self.callback()

class RewardedCallback(PythonJavaClass):
    __javainterfaces__ = ['com/google/android/gms/ads/rewarded/RewardedAdLoadCallback']
    __javacontext__ = 'app'

    def __init__(self, screen):
        super(RewardedCallback, self).__init__()
        self.screen = screen

    @java_method('(Lcom/google/android/gms/ads/rewarded/RewardedAd;)V')
    def onAdLoaded(self, rewardedAd):
        self.screen.anuncio_carregado = rewardedAd
        self.screen.ids.label_status_tempo.text = "Status: Anúncio pronto!"

    @java_method('(Lcom/google/android/gms/ads/LoadAdError;)V')
    def onAdFailedToLoad(self, loadAdError):
        self.screen.anuncio_carregado = None
        """)
    except Exception:
        pass

# Design das Telas em String KV Language
KV = '''
MDScreenManager:
    LoginScreen:
    CadastroScreen:
    HomeScreen:
    PagamentoScreen:
    AirdropScreen:
    AdMobTestScreen:

<LoginScreen>:
    name: "login"
    
    MDCard:
        orientation: "vertical"
        padding: "24dp"
        spacing: "14dp"
        size_hint: None, None
        size: "310dp", "480dp"
        pos_hint: {"center_x": .5, "center_y": .5}
        elevation: 4
        radius: [15, 15, 15, 15]

        MDLabel:
            text: "Bem-vindo"
            font_style: "H4"
            bold: True
            halign: "center"
            size_hint_y: None
            height: self.texture_size[1]
            theme_text_color: "Primary"

        MDLabel:
            text: "Faça login para continuar"
            font_style: "Subtitle2"
            halign: "center"
            size_hint_y: None
            height: self.texture_size[1]
            theme_text_color: "Secondary"

        MDTextField:
            id: login_email
            hint_text: "E-mail"
            helper_text: "Ex: usuario@email.com"
            helper_text_mode: "on_error"
            icon_right: "email"
            mode: "rectangle"

        AnchorLayout:
            size_hint_y: None
            height: "60dp"
            anchor_x: "right"
            anchor_y: "center"

            MDTextField:
                id: login_senha
                hint_text: "Senha"
                mode: "rectangle"
                password: True
                size_hint_x: 1

            MDIconButton:
                id: icone_olho_login
                icon: "eye-off"
                pos_hint: {"center_y": .5}
                theme_text_color: "Hint"
                on_release: root.alternar_olho_senha()

        MDFlatButton:
            text: "Esqueceu a senha?"
            pos_hint: {"right": 1}
            theme_text_color: "Custom"
            text_color: app.theme_cls.accent_color
            font_style: "Caption"
            on_release: root.recurar_senha()

        MDRaisedButton:
            text: "ENTRAR"
            size_hint_x: 1
            md_bg_color: app.theme_cls.primary_color
            on_release: root.fazer_login()

        MDFlatButton:
            text: "Não tem uma conta? Cadastre-se"
            pos_hint: {"center_x": .5}
            theme_text_color: "Custom"
            text_color: app.theme_cls.primary_color
            on_release: root.manager.current = "cadastro"

<CadastroScreen>:
    name: "cadastro"

    MDCard:
        orientation: "vertical"
        padding: "24dp"
        spacing: "12dp"
        size_hint: None, None
        size: "310dp", "550dp"
        pos_hint: {"center_x": .5, "center_y": .5}
        elevation: 4
        radius: [15, 15, 15, 15]

        MDLabel:
            text: "Criar Conta"
            font_style: "H4"
            bold: True
            halign: "center"
            size_hint_y: None
            height: self.texture_size[1]

        MDTextField:
            id: cad_nome
            hint_text: "Nome Completo"
            icon_right: "account"
            mode: "rectangle"

        MDTextField:
            id: cad_email
            hint_text: "E-mail"
            icon_right: "email"
            mode: "rectangle"

        AnchorLayout:
            size_hint_y: None
            height: "60dp"
            anchor_x: "right"
            anchor_y: "center"

            MDTextField:
                id: cad_senha
                hint_text: "Senha"
                helper_text: "Mínimo 8 dígitos com uma letra Maiúscula"
                helper_text_mode: "on_focus"
                password: True
                mode: "rectangle"
                size_hint_x: 1
                on_text: root.atualizar_barra_forca(self.text)

            MDIconButton:
                id: icone_olho_cadastro
                icon: "eye-off"
                pos_hint: {"center_y": .5}
                theme_text_color: "Hint"
                on_release: root.alternar_olho_cadastro()

        MDProgressBar:
            id: barra_forca
            value: 0
            max: 100
            size_hint_y: None
            height: "4dp"
            color: [0.8, 0.2, 0.2, 1]

        MDLabel:
            id: label_forca
            text: "Força da senha: Muito curta"
            font_style: "Caption"
            theme_text_color: "Secondary"

        MDRaisedButton:
            text: "CADASTRAR"
            size_hint_x: 1
            md_bg_color: app.theme_cls.primary_color
            on_release: root.registrar_usuario()

        MDFlatButton:
            text: "Voltar para o Login"
            pos_hint: {"center_x": .5}
            on_release: root.manager.current = "login"

<HomeScreen>:
    name: "home"

    BoxLayout:
        orientation: 'vertical'
        padding: "20dp"
        spacing: "20dp"

        MDLabel:
            id: boas_vindas
            text: "Olá! Bem-vindo ao sistema seguro."
            font_style: "H5"
            halign: "center"

        MDRaisedButton:
            text: "COLETAR AIRDROP (JAPCOINS)"
            pos_hint: {"center_x": .5}
            size_hint_x: 0.8
            md_bg_color: [0.1, 0.7, 0.3, 1]
            on_release: root.manager.current = "airdrop"

        MDRaisedButton:
            text: "IR PARA PAGAMENTO (USDT)"
            pos_hint: {"center_x": .5}
            size_hint_x: 0.8
            md_bg_color: app.theme_cls.accent_color
            on_release: root.manager.current = "pagamento"

        MDRaisedButton:
            text: "LOGOUT / SAIR"
            pos_hint: {"center_x": .5}
            size_hint_x: 0.8
            md_bg_color: [0.9, 0.2, 0.2, 1]
            on_release: root.logout()

<PagamentoScreen>:
    name: "pagamento"

    BoxLayout:
        orientation: "vertical"
        padding: "20dp"
        spacing: "12dp"

        MDLabel:
            text: "Pagamento via USDT (TRC20)"
            font_style: "H5"
            bold: True
            halign: "center"

        MDLabel:
            text: "Selecione o valor do depósito:"
            font_style: "Body2"
            theme_text_color: "Secondary"

        MDGridLayout:
            cols: 4
            spacing: "8dp"
            size_hint_y: None
            height: "45dp"

            MDRoundFlatButton:
                id: btn_1
                text: "1 USDT"
                size_hint_x: 1
                on_release: root.selecionar_valor(1, self)

            MDRoundFlatButton:
                id: btn_5
                text: "5 USDT"
                size_hint_x: 1
                on_release: root.selecionar_valor(5, self)

            MDRoundFlatButton:
                id: btn_10
                text: "10 USDT"
                size_hint_x: 1
                md_bg_color: app.theme_cls.primary_color
                text_color: 1, 1, 1, 1
                on_release: root.selecionar_valor(10, self)

            MDRoundFlatButton:
                id: btn_50
                text: "50 USDT"
                size_hint_x: 1
                on_release: root.selecionar_valor(50, self)

        MDTextField:
            id: valor_usdt
            hint_text: "Valor Selecionado"
            text: "10.00"
            readonly: True
            mode: "rectangle"

        MDRaisedButton:
            text: "GERAR ENDEREÇO DE DEPÓSITO"
            size_hint_x: 1
            on_release: root.gerar_cobranca_usdt()

        MDCard:
            orientation: "vertical"
            padding: "16dp"
            size_hint_y: None
            height: "170dp"
            radius: [10,]
            elevation: 2

            MDLabel:
                text: "Dados para Transferência (Rede TRC20):"
                bold: True
                font_style: "Caption"

            MDTextField:
                id: endereco_carteira
                text: "Clique em gerar botão acima..."
                readonly: True
                mode: "fill"

            MDLabel:
                id: status_pagamento
                text: "Status: Aguardando geração"
                halign: "center"
                bold: True
                theme_text_color: "Secondary"

        MDRaisedButton:
            text: "VERIFICAR PAGAMENTO"
            size_hint_x: 1
            md_bg_color: app.theme_cls.primary_color
            on_release: root.verificar_status_deposito()

        MDFlatButton:
            text: "Voltar para Home"
            pos_hint: {"center_x": .5}
            on_release: root.manager.current = "home"

<AirdropScreen>:
    name: "airdrop"
    on_enter: root.ao_entrar_na_tela()

    BoxLayout:
        orientation: "vertical"
        padding: "24dp"
        spacing: "20dp"

        MDLabel:
            text: "Japcoins Airdrop 🚀"
            font_style: "H4"
            bold: True
            halign: "center"
            theme_text_color: "Primary"

        MDCard:
            orientation: "vertical"
            padding: "16dp"
            size_hint_y: None
            height: "120dp"
            radius: [15,]
            md_bg_color: [0.95, 0.95, 0.95, 1]
            elevation: 1

            MDLabel:
                text: "Seu Saldo Atual:"
                halign: "center"
                font_style: "Subtitle1"
                theme_text_color: "Secondary"

            MDLabel:
                id: saldo_japcoins
                text: "0.00 JAP"
                halign: "center"
                font_style: "H3"
                bold: True
                theme_text_color: "Custom"
                text_color: [0.1, 0.6, 0.2, 1]

        MDLabel:
            id: label_status_tempo
            text: "Status: Pronto para assistir"
            halign: "center"
            font_style: "Body1"

        MDProgressBar:
            id: barra_progresso_tempo
            value: 0
            max: 100
            size_hint_y: None
            height: "6dp"

        MDRaisedButton:
            id: btn_coletar
            text: "ASSISTIR E COLETAR +1 JAP"
            size_hint_x: 1
            height: "50dp"
            md_bg_color: [0.1, 0.7, 0.3, 1]
            on_release: root.disparar_clique_propaganda()

        MDFlatButton:
            text: "Voltar para Home"
            pos_hint: {"center_x": .5}
            on_release: root.voltar_home()

<AdMobTestScreen>:
    name: "admob_test_screen"
    
    MDFloatLayout:
        md_bg_color: [0, 0, 0, 0.95]

        MDLabel:
            text: "Google AdMob Test Ad (Recompensado)"
            font_style: "H5"
            bold: True
            halign: "center"
            pos_hint: {"center_x": .5, "center_y": .85}
            theme_text_color: "Custom"
            text_color: [1, 1, 1, 1]

        MDIconButton:
            icon: "video-player"
            icon_size: "80dp"
            pos_hint: {"center_x": .5, "center_y": .55}
            theme_text_color: "Custom"
            text_color: app.theme_cls.accent_color

        MDLabel:
            id: label_tempo_propaganda
            text: "O seu prêmio será liberado em 5 segundos..."
            halign: "center"
            pos_hint: {"center_x": .5, "center_y": .3}
            theme_text_color: "Custom"
            text_color: [0.9, 0.9, 0.9, 1]

        MDProgressBar:
            id: progresso_propaganda
            max: 5
            value: 0
            size_hint_x: 0.8
            pos_hint: {"center_x": .5, "center_y": .2}
            color: app.theme_cls.accent_color
'''

class LoginScreen(MDScreen):
    def alternar_olho_senha(self):
        campo = self.ids.login_senha
        botao = self.ids.icone_olho_login
        texto_atual = campo.text
        campo.password = not campo.password
        botao.icon = "eye" if not campo.password else "eye-off"
        campo._refresh_text(texto_atual)

    def fazer_login(self):
        email = self.ids.login_email.text.strip()
        senha = self.ids.login_senha.text.strip()

        if not email or not senha:
            self.mostrar_erro("Preencha todos os campos!")
            return

        payload = {"email": email, "password": senha, "returnSecureToken": True}

        try:
            resposta_auth = requests.post(AUTH_LOGIN_URL, json=payload)
            dados_auth = resposta_auth.json()

            if resposta_auth.status_code == 200:
                local_id = dados_auth["localId"]
                resposta_db = requests.get(f"{FIREBASE_URL}usuarios/{local_id}.json")
                
                if resposta_db.status_code == 200 and resposta_db.json() is not None:
                    nome_usuario = resposta_db.json().get("nome", "Usuário")
                else:
                    nome_usuario = email.split('@')[0]

                self.manager.get_screen("home").ids.boas_vindas.text = f"Bem-vindo,\n{nome_usuario}!"
                self.manager.get_screen("airdrop").local_id_usuario = local_id
                self.manager.current = "home"
                self.limpar_campos()
            else:
                erro_msg = dados_auth.get("error", {}).get("message", "Erro desconhecido")
                if erro_msg == "INVALID_PASSWORD":
                    self.mostrar_erro("Senha incorreta.")
                elif erro_msg == "EMAIL_NOT_FOUND":
                    self.mostrar_erro("E-mail não cadastrado.")
                else:
                    self.mostrar_erro(f"Falha: {erro_msg}")
        except Exception as e:
            self.mostrar_erro("Erro de conexão com o servidor.")

    def recurar_senha(self):
        email = self.ids.login_email.text.strip()
        if not email or "@" not in email:
            self.mostrar_erro("Digite um e-mail válido no campo acima primeiro!")
            return

        payload = {"requestType": "PASSWORD_RESET", "email": email}

        try:
            resposta = requests.post(AUTH_RESET_URL, json=payload)
            if resposta.status_code == 200:
                self.mostrar_mensagem_sucesso(f"E-mail de recuperação enviado para:\n{email}")
            else:
                erro_msg = resposta.json().get("error", {}).get("message", "Erro")
                self.mostrar_erro(f"Falha: {erro_msg}")
        except:
            self.mostrar_erro("Erro de rede ao recuperar senha.")

    def mostrar_erro(self, texto):
        snackbar = MDSnackbar(md_bg_color=(0.8, 0.2, 0.2, 1))
        snackbar.add_widget(MDLabel(text=texto, theme_text_color="Custom", text_color=(1, 1, 1, 1)))
        snackbar.open()

    def mostrar_mensagem_sucesso(self, texto):
        snackbar = MDSnackbar(md_bg_color=(0.2, 0.6, 0.2, 1))
        snackbar.add_widget(MDLabel(text=texto, theme_text_color="Custom", text_color=(1, 1, 1, 1)))
        snackbar.open()

    def limpar_campos(self):
        self.ids.login_email.text = ""
        self.ids.login_senha.text = ""
        self.ids.login_senha.password = True
        self.ids.icone_olho_login.icon = "eye-off"


class CadastroScreen(MDScreen):
    def alternar_olho_cadastro(self):
        campo = self.ids.cad_senha
        botao = self.ids.icone_olho_cadastro
        texto_atual = campo.text
        campo.password = not campo.password
        botao.icon = "eye" if not campo.password else "eye-off"
        campo._refresh_text(texto_atual)

    def atualizar_barra_forca(self, senha):
        if len(senha) == 0:
            self.ids.barra_forca.value = 0
            self.ids.label_forca.text = "Força da senha: Muito curta"
            self.ids.barra_forca.color = [0.8, 0.2, 0.2, 1]
            return
        tem_maiuscula = any(c.isupper() for c in senha)
        comprimento_valido = len(senha) >= 8

        if comprimento_valido and tem_maiuscula:
            self.ids.barra_forca.value = 100
            self.ids.label_forca.text = "Força da senha: Forte ✅"
            self.ids.barra_forca.color = [0.2, 0.6, 0.2, 1]
        elif comprimento_valido or tem_maiuscula:
            self.ids.barra_forca.value = 50
            self.ids.label_forca.text = "Força da senha: Média (Falta maiúscula ou tamanho)"
            self.ids.barra_forca.color = [0.9, 0.6, 0.1, 1]
        else:
            self.ids.barra_forca.value = 20
            self.ids.label_forca.text = "Força da senha: Fraca"
            self.ids.barra_forca.color = [0.8, 0.2, 0.2, 1]

    def registrar_usuario(self):
        nome = self.ids.cad_nome.text.strip()
        email = self.ids.cad_email.text.strip()
        senha = self.ids.cad_senha.text.strip()

        if not nome or not email or not senha:
            self.mostrar_mensagem("Preencha todos os campos!", erro=True)
            return
        if len(senha) < 8 or not any(c.isupper() for c in senha):
            self.mostrar_mensagem("A senha necessita de 8 dígitos e 1 letra maiúscula.", erro=True)
            return

        payload = {"email": email, "password": senha, "returnSecureToken": True}

        try:
            resposta_auth = requests.post(AUTH_REGISTER_URL, json=payload)
            if resposta_auth.status_code == 200:
                local_id = resposta_auth.json()["localId"]
                dados_usuario = {"nome": nome, "email": email, "japcoins": 0}
                requests.put(f"{FIREBASE_URL}usuarios/{local_id}.json", data=json.dumps(dados_usuario))
                self.mostrar_mensagem("Cadastro realizado com sucesso!", erro=False)
                self.limpar_campos()
                self.manager.current = "login"
            else:
                self.mostrar_mensagem("Este e-mail já pode estar em uso.", erro=True)
        except:
            self.mostrar_mensagem("Erro de conexão.", erro=True)

    def mostrar_mensagem(self, texto, erro=False):
        cor = (0.2, 0.6, 0.2, 1) if not erro else (0.8, 0.2, 0.2, 1)
        snackbar = MDSnackbar(md_bg_color=cor)
        snackbar.add_widget(MDLabel(text=texto, theme_text_color="Custom", text_color=(1, 1, 1, 1)))
        snackbar.open()

    def limpar_campos(self):
        self.ids.cad_nome.text = ""
        self.ids.cad_email.text = ""
        self.ids.cad_senha.text = ""
        self.ids.barra_forca.value = 0


class HomeScreen(MDScreen):
    def logout(self):
        self.manager.current = "login"


class PagamentoScreen(MDScreen):
    def selecionar_valor(self, valor, botao_clicado):
        self.ids.valor_usdt.text = f"{valor}.00"
        botoes = [self.ids.btn_1, self.ids.btn_5, self.ids.btn_10, self.ids.btn_50]
        for btn in botoes:
            if btn == botao_clicado:
                btn.md_bg_color = MDApp.get_running_app().theme_cls.primary_color
                btn.text_color = (1, 1, 1, 1)
            else:
                btn.md_bg_color = (0, 0, 0, 0)
                btn.text_color = MDApp.get_running_app().theme_cls.primary_color

    def obtener_timestamp_binance(self):
        try:
            res = requests.get(f"{BINANCE_BASE_URL}/api/v3/time", timeout=5)
            if res.status_code == 200:
                return res.json()["serverTime"]
        except:
            pass
        return int(time.time() * 1000)

    def gerenciar_assinatura_hmac(self, query_string):
        return hmac.new(BINANCE_SECRET_KEY.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

    def gerar_cobranca_usdt(self):
        timestamp = self.obtener_timestamp_binance()
        query_string = f"coin=USDT&network=TRX&recvWindow=60000&timestamp={timestamp}"
        params = {
            "coin": "USDT", "network": "TRX", "recvWindow": 60000,
            "timestamp": timestamp, "signature": self.gerenciar_assinatura_hmac(query_string)
        }
        headers = {"X-MBX-APIKEY": BINANCE_API_KEY, "Content-Type": "application/json"}
        
        try:
            resposta = requests.get(f"{BINANCE_BASE_URL}/sapi/v1/capital/deposit/address", params=params, headers=headers)
            if resposta.status_code == 200:
                self.ids.endereco_carteira.text = resposta.json()["address"]
                self.ids.status_pagamento.text = f"Status: Envie {self.ids.valor_usdt.text} USDT"
            else:
                self.ids.endereco_carteira.text = "Verifique suas chaves Binance API."
        except:
            self.ids.endereco_carteira.text = "Erro na rede."

    def verificar_status_deposito(self):
        timestamp = self.obtener_timestamp_binance()
        query_string = f"coin=USDT&recvWindow=60000&status=1&timestamp={timestamp}"
        params = {
            "coin": "USDT", "status": 1, "recvWindow": 60000,
            "timestamp": timestamp, "signature": self.gerenciar_assinatura_hmac(query_string)
        }
        headers = {"X-MBX-APIKEY": BINANCE_API_KEY}
        
        try:
            resposta = requests.get(f"{BINANCE_BASE_URL}/sapi/v1/capital/deposit/hisrec", params=params, headers=headers)
            historico = resposta.json()
            if resposta.status_code == 200 and isinstance(historico, list):
                valor_esperado = float(self.ids.valor_usdt.text)
                endereco_seu = self.ids.endereco_carteira.text
                pago = any(d["address"] == endereco_seu and d.get("network") == "TRX" and float(d["amount"]) >= valor_esperado for d in historico)
                
                if pago:
                    self.ids.status_pagamento.text = "Status: ✅ PAGO E CONFIRMADO!"
                else:
                    self.ids.status_pagamento.text = "Status: ⏳ Depósito não detectado."
        except:
            pass


class AirdropScreen(MDScreen):
    local_id_usuario = ""
    tempo_restante = 5
    evento_relogio = None
    anuncio_carregado = None 

    def ao_entrar_na_tela(self):
        threading.Thread(target=self.puxar_saldo_firebase, daemon=True).start()
        self.ids.btn_coletar.disabled = False
        self.ids.btn_coletar.text = "ASSISTIR E COLETAR +1 JAP"
        self.ids.label_status_tempo.text = "Status: Pronto para assistir"
        self.ids.barra_progresso_tempo.value = 0
        
        if platform == "android":
            Clock.schedule_once(lambda dt: self.carregar_anuncio_admob(), 0.5)

    def puxar_saldo_firebase(self):
        if not self.local_id_usuario:
            return
        try:
            res = requests.get(f"{FIREBASE_URL}usuarios/{self.local_id_usuario}/japcoins.json")
            if res.status_code == 200 and res.text != 'null':
                Clock.schedule_once(lambda dt: self._atualizar_label_saldo(res.text), 0)
        except:
            pass

    def _atualizar_label_saldo(self, texto):
        self.ids.saldo_japcoins.text = f"{float(texto):.2f} JAP"

    def carregar_anuncio_admob(self):
        if platform == "android" and AdRequest is not None and RewardedAd is not None and RewardedCallback is not None:
            try:
                activity = PythonActivity.mActivity
                requisicao = AdRequest.Builder().build()
                ad_unit_id = "ca-app-pub-3940256099942544/5224354917"
                activity.runOnUiThread(lambda: RewardedAd.load(
                    activity, ad_unit_id, requisicao, RewardedCallback(self)
                ))
            except Exception:
                self.anuncio_carregado = None

    def disparar_clique_propaganda(self):
        self.ids.btn_coletar.disabled = True
        self.ids.label_status_tempo.text = "Status: Carregando..."
        
        if platform == "android" and self.anuncio_carregado and RecompensaListener is not None:
            try:
                activity = PythonActivity.mActivity
                listener = RecompensaListener(self.fechar_propaganda_e_premiar)
                activity.runOnUiThread(lambda: self.anuncio_carregado.show(activity, listener))
            except Exception:
                self.ir_para_tela_simulador()
        else:
            self.ir_para_tela_simulador()

    def ir_para_tela_simulador(self):
        self.manager.transition = NoTransition()
        self.manager.current = "admob_test_screen"
        self.manager.get_screen("admob_test_screen").iniciar_cronometro_anuncio(self)

    def fechar_propaganda_e_premiar(self):
        try:
            saldo_atual = float(self.ids.saldo_japcoins.text.split(" ")[0])
        except Exception:
            saldo_atual = 0.0
            
        novo_saldo = saldo_atual + 1.00
        self.ids.saldo_japcoins.text = f"{novo_saldo:.2f} JAP"
        
        if self.local_id_usuario:
            threading.Thread(target=lambda: requests.put(f"{FIREBASE_URL}usuarios/{self.local_id_usuario}/japcoins.json", data=str(novo_saldo)), daemon=True).start()
                
        snackbar = MDSnackbar(md_bg_color=(0.1, 0.6, 0.2, 1))
        snackbar.add_widget(MDLabel(text="Parabéns! +1 Japcoin adicionado.", theme_text_color="Custom", text_color=(1,1,1,1)))
        snackbar.open()
        
        self.anuncio_carregado = None
        self.iniciar_contagem_bloqueio()

    def iniciar_contagem_bloqueio(self):
        self.tempo_restante = 5
        self.ids.btn_coletar.disabled = True
        self.ids.btn_coletar.text = "AGUARDE BLOQUEIO..."
        self.ids.label_status_tempo.text = f"Próximo anúncio em: {self.tempo_restante}s"
        self.ids.barra_progresso_tempo.value = 100
        
        if self.evento_relogio:
            Clock.unschedule(self.evento_relogio)
        self.evento_relogio = Clock.schedule_interval(self.atualizar_relogio_bloqueio, 1)

    def atualizar_relogio_bloqueio(self, dt):
        self.tempo_restante -= 1
        if self.tempo_restante <= 0:
            self.ids.label_status_tempo.text = "Status: Pronto para assistir"
            self.ids.barra_progresso_tempo.value = 0
            self.ids.btn_coletar.disabled = False
            self.ids.btn_coletar.text = "ASSISTIR E COLETAR +1 JAP"
            Clock.unschedule(self.evento_relogio)
            if platform == "android":
                Clock.schedule_once(lambda dt: self.carregar_anuncio_admob(), 0.1)
        else:
            self.ids.label_status_tempo.text = f"Próximo anúncio em: {self.tempo_restante}s"
            self.ids.barra_progresso_tempo.value = (self.tempo_restante / 5) * 100

    def voltar_home(self):
        if self.evento_relogio:
            Clock.unschedule(self.evento_relogio)
        self.manager.current = "home"


class AdMobTestScreen(MDScreen):
    ref_airdrop = None
    tempo_ad = 5
    evento_propaganda = None

    def iniciar_cronometro_anuncio(self, ref_airdrop):
        self.ref_airdrop = ref_airdrop
        self.tempo_ad = 5
        self.ids.progresso_propaganda.value = 0
        self.ids.label_tempo_propaganda.text = "O seu prêmio será liberado em 5 segundos..."
        
        if self.evento_propaganda:
            Clock.unschedule(self.evento_propaganda)
        self.evento_propaganda = Clock.schedule_interval(self.atualizar_propaganda, 1)

    def atualizar_propaganda(self, dt):
        self.tempo_ad -= 1
        self.ids.progresso_propaganda.value = 5 - self.tempo_ad
        
        if self.tempo_ad <= 0:
            Clock.unschedule(self.evento_propaganda)
            self.manager.transition = NoTransition()
            self.manager.current = "airdrop"
            if self.ref_airdrop:
                self.ref_airdrop.fechar_propaganda_e_premiar()
        else:
            self.ids.label_tempo_propaganda.text = f"O seu prêmio será liberado em {self.tempo_ad} segundos..."


class SistemaLoginApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.accent_palette = "Amber"
        self.theme_cls.theme_style = "Light"
        return Builder.load_string(KV)

if __name__ == "__main__":
    SistemaLoginApp().run()