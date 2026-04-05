# EasySport

## Visão Geral

O EasySport é uma aplicação web desenvolvida em Flask para facilitar a reserva e gestão de espaços desportivos.

A plataforma permite a utilização por dois tipos de utilizadores:
- clientes, que podem consultar espaços, efetuar reservas e acompanhar o estado das suas reservas
- administradores, que podem gerir utilizadores, espaços, reservas e pagamentos

O objetivo do projeto é simular uma plataforma de reservas desportivas simples, organizada e funcional, com uma interface moderna e fácil de utilizar.

---

## Funcionalidades

### Utilizador
- registo de conta
- login e logout
- consulta de espaços disponíveis
- reserva de espaços
- consulta das suas reservas
- cancelamento de reservas pendentes
- pagamento de reservas pendentes
- edição do perfil

### Administrador
- login com acesso ao painel de administração
- consulta de indicadores principais do sistema
- gestão de utilizadores(ativação e desativação de utilizadores)
- gestão de espaços (criação, edição, ativação e desativação)
- consulta de reservas
- consulta de pagamentos

---

## Funcionalidades adicionais

- interface adaptada a diferentes páginas do sistema
- separação visual entre área pública, utilizador e administrador
- mensagens de feedback para ações como login, registo, edição e reserva
- imagens associadas aos espaços
- apresentação dinâmica de espaços em destaque
- formulários melhorados para evitar perda de dados em caso de erro
- sistema preparado para evolução da reserva com calendário, horários disponíveis e duração dinâmica

---

## Tecnologias Utilizadas

- **Python**  
  linguagem principal da aplicação

- **Flask**  
  framework web usada para construir a aplicação

- **Jinja**  
  sistema que permite meter dados do Python dentro do HTML

- **HTML / CSS**  
  estrutura e estilo da interface

- **JavaScript**  
  interatividade no frontend, como dropdowns, para validações, mensagens e seleção de horários na reserva.

- **SQLite**  
  base de dados usada para guardar a informação do projeto

- **SQLAlchemy**  
  para fazer a ligação entre o Flask e a base de dados

---

## Melhorias Futuras
1. Na Página Inicial do admin adicionar a opção de ver estatisticas do sistema 
2. Adicionar a hipótese do cliente adicionar foto ao perfil
3. Adicionar notificações em falta


## Guia de Instalação 

1. Extrai a pasta do projeto 
2. No VS Code abre a pasta com o nome "Projeto_EasySport
3. Abre o terminal 
4. Para criar um ambiente virtual: No Windows: python -m venv venv   |  No Mac/Linux: python3 -m venv venv
5. Para ativar o ambiente virtual: No Windows: venv\Scripts\activate |  No Mac/Linux: source venv/bin/activate
6. Para instalar as bibliotecas do projeto: pip install -r requirements.txt
7. Para executar o projeto: python run.py
8. Depois abre no navegador: http://127.0.0.1:5000

