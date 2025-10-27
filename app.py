import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import random

# Configuración de la página
st.set_page_config(
    page_title="Alivia - Tu Aliado Financiero IA",
    page_icon="💰",
    layout="wide"
)

# Inicializar estado de sesión
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.connected_accounts = False
    st.session_state.scan_complete = False
    st.session_state.total_saved = 0
    st.session_state.monthly_income = 3500
    st.session_state.chat_history = []
    
    # Datos de ejemplo para suscripciones
    st.session_state.subscriptions = [
        {"nombre": "Gimnasio Premium", "costo": 45, "uso": "Última visita hace 4 meses", "activo": True},
        {"nombre": "Streaming Plus", "costo": 15.99, "uso": "Sin uso en 2 meses", "activo": True},
        {"nombre": "Cloud Storage Pro", "costo": 9.99, "uso": "Usando solo 10% del espacio", "activo": True},
        {"nombre": "Revista Digital", "costo": 6.99, "uso": "Sin abrir en 3 meses", "activo": True},
    ]
    
    # Datos de gastos para análisis
    st.session_state.expenses = pd.DataFrame({
        'Categoría': ['Vivienda', 'Alimentación', 'Transporte', 'Entretenimiento', 'Suscripciones', 'Servicios', 'Otros'],
        'Monto': [1200, 450, 280, 180, 78, 320, 150]
    })

# CSS personalizado
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .tagline {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .savings-highlight {
        font-size: 2.5rem;
        font-weight: bold;
        color: #10b981;
    }
    .feature-box {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">💰 Alivia</h1>', unsafe_allow_html=True)
st.markdown('<p class="tagline">Tu Aliado Financiero IA - Combate el estrés económico automáticamente</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/150x150/667eea/ffffff?text=Alivia", width=150)
    st.markdown("### 🎯 Navegación")
    page = st.radio(
        "Selecciona una sección:",
        ["🏠 Inicio", "🔍 Detector de Fugas", "🤖 Copiloto IA", "💵 Generador de Ingresos", "📊 Mi Dashboard"]
    )
    
    st.markdown("---")
    st.markdown("### 💎 Tu Cuenta")
    if st.session_state.total_saved > 0:
        st.success(f"**Ahorrado este mes:**\n${st.session_state.total_saved:.2f}")
    
    plan = st.selectbox("Plan actual:", ["Gratuito", "Premium ($7/mes)"])
    
    if plan == "Gratuito":
        st.info("✨ Mejora a Premium para acciones automatizadas ilimitadas")

# Página de Inicio
if page == "🏠 Inicio":
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
            <div class="metric-card">
                <h3>🎯 Ahorros Detectados</h3>
                <div class="savings-highlight">$127</div>
                <p>Este mes</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="metric-card">
                <h3>⏱️ Tiempo Ahorrado</h3>
                <div class="savings-highlight">12h</div>
                <p>En gestión financiera</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div class="metric-card">
                <h3>💡 Oportunidades</h3>
                <div class="savings-highlight">5</div>
                <p>De ingresos extra</p>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Onboarding rápido
    if not st.session_state.connected_accounts:
        st.markdown("### 🚀 Comienza en 3 Pasos")
        
        st.markdown("""
        <div class="feature-box">
            <h4>📱 Paso 1: Conecta tus cuentas de forma segura</h4>
            <p>Conecta tus bancos y tarjetas para que Alivia analice tus finanzas (conexión encriptada de nivel bancario)</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔗 Conectar Cuentas Ahora", type="primary", use_container_width=True):
            with st.spinner("Conectando de forma segura..."):
                import time
                time.sleep(2)
                st.session_state.connected_accounts = True
                st.rerun()
    
    else:
        if not st.session_state.scan_complete:
            st.markdown("### 🔍 Escaneando tus finanzas...")
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            steps = [
                "Analizando transacciones...",
                "Identificando suscripciones...",
                "Detectando cobros duplicados...",
                "Buscando oportunidades de ahorro...",
                "¡Análisis completo!"
            ]
            
            for i, step in enumerate(steps):
                status_text.text(step)
                progress_bar.progress((i + 1) * 20)
                import time
                time.sleep(0.5)
            
            st.session_state.scan_complete = True
            st.balloons()
            st.rerun()
        
        else:
            st.success("✅ ¡Análisis completo! Hemos encontrado oportunidades para ahorrar **$127 al mes**")
            
            st.markdown("### 🎯 Acciones Recomendadas")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                <div class="feature-box">
                    <h4>💸 Cancelar suscripciones no usadas</h4>
                    <p>Ahorro potencial: <strong>$77.97/mes</strong></p>
                    <p>4 suscripciones detectadas sin uso reciente</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Ver Detalles →", key="sub1"):
                    st.session_state.page = "🔍 Detector de Fugas"
            
            with col2:
                st.markdown("""
                <div class="feature-box">
                    <h4>💰 Generar ingresos extra</h4>
                    <p>Potencial: <strong>$300-500/mes</strong></p>
                    <p>5 oportunidades basadas en tu perfil</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Explorar Opciones →", key="income1"):
                    st.session_state.page = "💵 Generador de Ingresos"

# Página Detector de Fugas
elif page == "🔍 Detector de Fugas":
    st.markdown("## 🔍 Detector de Fugas de Dinero")
    st.markdown("Identifica gastos innecesarios y ahorra desde la primera semana")
    
    st.markdown("---")
    
    # Resumen de ahorros
    total_leak = sum([sub['costo'] for sub in st.session_state.subscriptions if sub['activo']])
    st.markdown(f"### 💡 Ahorro potencial detectado: **${total_leak:.2f}/mes**")
    
    st.markdown("#### 📱 Suscripciones sin Uso")
    
    for i, sub in enumerate(st.session_state.subscriptions):
        if sub['activo']:
            col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
            
            with col1:
                st.markdown(f"**{sub['nombre']}**")
                st.caption(sub['uso'])
            
            with col2:
                st.metric("Costo mensual", f"${sub['costo']}")
            
            with col3:
                st.metric("Ahorro anual", f"${sub['costo']*12:.0f}")
            
            with col4:
                if st.button("❌ Cancelar", key=f"cancel_{i}"):
                    st.session_state.subscriptions[i]['activo'] = False
                    st.session_state.total_saved += sub['costo']
                    st.success(f"✅ {sub['nombre']} cancelado. ¡Ahorrarás ${sub['costo']}/mes!")
                    st.rerun()
            
            st.markdown("---")
    
    # Otras oportunidades
    st.markdown("#### 🎯 Otras Oportunidades de Ahorro")
    
    opportunities = [
        {"título": "Tarifa bancaria elevada", "ahorro": "$12/mes", "acción": "Cambiar a cuenta sin comisiones"},
        {"título": "Seguro de auto sobrevalorado", "ahorro": "$25/mes", "acción": "Renegociar con IA Alivia"},
        {"título": "Plan de datos móvil excesivo", "ahorro": "$15/mes", "acción": "Optimizar plan según uso real"},
    ]
    
    for opp in opportunities:
        with st.expander(f"💰 {opp['título']} - Ahorra {opp['ahorro']}"):
            st.write(f"**Acción recomendada:** {opp['acción']}")
            st.button("🤖 Dejar que IA lo gestione", key=f"ai_{opp['título']}")

# Página Copiloto IA
elif page == "🤖 Copiloto IA":
    st.markdown("## 🤖 Copiloto Financiero Inteligente")
    st.markdown("Tu asesor personal 24/7 - Pregunta lo que necesites")
    
    st.markdown("---")
    
    # Sugerencias rápidas
    st.markdown("#### 💡 Preguntas Frecuentes")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💡 ¿Cómo bajar mi factura de luz?"):
            st.session_state.chat_history.append({
                "user": "¿Cómo puedo bajar mi factura de luz?",
                "ai": "Basándome en tu consumo, te recomiendo: 1) Cambiar a bombillas LED (ahorro ~$8/mes), 2) Ajustar termostato 2°C (ahorro ~$15/mes), 3) Desenchufar aparatos en standby (ahorro ~$5/mes). Total: **$28/mes de ahorro**. ¿Quieres que busque proveedores con mejores tarifas en tu zona?"
            })
    
    with col2:
        if st.button("🎯 ¿Qué puedo recortar sin sacrificar?"):
            st.session_state.chat_history.append({
                "user": "¿Qué puedo recortar este mes sin dejar de disfrutar?",
                "ai": "He analizado tus hábitos. Puedes: 1) Reducir delivery (cocinas bien, pides por comodidad) → Ahorro $60/mes, 2) Cambiar streaming premium a estándar (rara vez usas 4K) → Ahorro $5/mes, 3) Gym → clases al aire libre gratis → Ahorro $45/mes. **Total: $110/mes** manteniendo tu calidad de vida."
            })
    
    with col3:
        if st.button("📊 Crear presupuesto personalizado"):
            st.session_state.chat_history.append({
                "user": "Ayúdame a crear un presupuesto",
                "ai": "He creado un presupuesto basado en tus ingresos ($3,500/mes) y patrones reales de gasto. Regla 50/30/20 adaptada: **Necesidades** (55%: $1,925), **Gustos** (25%: $875), **Ahorros** (20%: $700). Te notificaré si te desvías. ¿Quieres ajustar alguna categoría?"
            })
    
    st.markdown("---")
    
    # Chat interface
    st.markdown("#### 💬 Chatea con tu Copiloto IA")
    
    # Mostrar historial
    for msg in st.session_state.chat_history:
        with st.chat_message("user"):
            st.write(msg["user"])
        with st.chat_message("assistant"):
            st.write(msg["ai"])
    
    # Input del usuario
    user_input = st.chat_input("Escribe tu pregunta financiera...")
    
    if user_input:
        # Respuestas simuladas de IA
        responses = {
            "ahorrar": "He analizado tus gastos y encontré 3 áreas de mejora inmediata: 1) Suscripciones no usadas ($78/mes), 2) Comisiones bancarias evitables ($12/mes), 3) Optimización de seguros ($25/mes). **Total ahorro potencial: $115/mes**.",
            "inversión": "Con tu perfil de ahorro actual de $700/mes, recomiendo: 60% en fondo indexado diversificado, 30% en cuenta de ahorro de alto rendimiento, 10% en cripto (solo lo que puedas perder). Esto balances crecimiento y seguridad.",
            "deuda": "Prioriza pagar primero la tarjeta con mayor interés (23% APR). Si transfieres el balance a una tarjeta 0% APR por 12 meses, ahorrarás $340 en intereses. ¿Quieres que busque ofertas de transferencia de balance?",
            "default": f"Entiendo tu consulta sobre '{user_input}'. Basándome en tu situación financiera actual, te sugiero revisar tu presupuesto en esa área. ¿Quieres que analice tus gastos específicos relacionados con esto?"
        }
        
        # Determinar respuesta
        response = responses["default"]
        for key in responses:
            if key in user_input.lower():
                response = responses[key]
                break
        
        st.session_state.chat_history.append({
            "user": user_input,
            "ai": response
        })
        st.rerun()

# Página Generador de Ingresos
elif page == "💵 Generador de Ingresos":
    st.markdown("## 💵 Generador de Ingresos Extra")
    st.markdown("Oportunidades personalizadas según tus habilidades y tiempo")
    
    st.markdown("---")
    
    # Oportunidades rankeadas
    opportunities = [
        {
            "titulo": "🚗 Conductor de Delivery Weekend",
            "ingreso": "$300-400/mes",
            "tiempo": "8-10h/mes (sábados)",
            "esfuerzo": "Bajo",
            "match": "95%",
            "porque": "Tienes auto, licencia vigente y fines de semana libres"
        },
        {
            "titulo": "🌐 Tutor de Inglés Online",
            "ingreso": "$400-600/mes",
            "tiempo": "12h/mes (tardes)",
            "esfuerzo": "Medio",
            "match": "88%",
            "porque": "Nivel avanzado de inglés detectado en tu perfil"
        },
        {
            "titulo": "📦 Vender Artículos en Desuso",
            "ingreso": "$150-250",
            "tiempo": "5h (una sola vez)",
            "esfuerzo": "Bajo",
            "match": "82%",
            "porque": "Objetos de valor detectados sin uso en 6+ meses"
        },
        {
            "titulo": "💻 Freelance Diseño Gráfico",
            "ingreso": "$200-500/mes",
            "tiempo": "15-20h/mes",
            "esfuerzo": "Medio-Alto",
            "match": "75%",
            "porque": "Habilidades en Adobe detectadas en tu perfil"
        },
        {
            "titulo": "🏠 Airbnb de Habitación Libre",
            "ingreso": "$350-500/mes",
            "tiempo": "2h/mes",
            "esfuerzo": "Bajo",
            "match": "70%",
            "porque": "Habitación disponible en zona turística"
        }
    ]
    
    st.markdown("### 🎯 Top Oportunidades para Ti")
    st.caption("Ordenadas por impacto económico vs. esfuerzo")
    
    for i, opp in enumerate(opportunities):
        with st.expander(f"{'⭐' * (5 - i//2)} {opp['titulo']} - {opp['ingreso']} | Match: {opp['match']}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**💰 Ingreso estimado:** {opp['ingreso']}")
                st.markdown(f"**⏱️ Tiempo requerido:** {opp['tiempo']}")
                st.markdown(f"**🎯 Nivel de esfuerzo:** {opp['esfuerzo']}")
            
            with col2:
                st.markdown(f"**📊 Match con tu perfil:** {opp['match']}")
                st.markdown(f"**💡 Por qué es ideal:**")
                st.info(opp['porque'])
            
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.button("✅ Me interesa", key=f"int_{i}", use_container_width=True)
            with col_b:
                st.button("📚 Más info", key=f"info_{i}", use_container_width=True)
            with col_c:
                st.button("❌ No por ahora", key=f"no_{i}", use_container_width=True)
    
    st.markdown("---")
    
    st.markdown("### 📈 Tu Potencial de Ingresos Extra")
    
    income_data = pd.DataFrame({
        'Oportunidad': [opp['titulo'].split(' ', 1)[1] for opp in opportunities[:3]],
        'Ingreso Mínimo': [300, 400, 150],
        'Ingreso Máximo': [400, 600, 250]
    })
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='Ingreso Mínimo',
        x=income_data['Oportunidad'],
        y=income_data['Ingreso Mínimo'],
        marker_color='#667eea'
    ))
    fig.add_trace(go.Bar(
        name='Ingreso Máximo',
        x=income_data['Oportunidad'],
        y=income_data['Ingreso Máximo'],
        marker_color='#764ba2'
    ))
    
    fig.update_layout(
        title='Potencial de Ingresos Extra (Top 3 Oportunidades)',
        xaxis_title='Oportunidad',
        yaxis_title='Ingreso Mensual ($)',
        barmode='group',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Página Dashboard
elif page == "📊 Mi Dashboard":
    st.markdown("## 📊 Mi Dashboard Financiero")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💰 Ingresos", f"${st.session_state.monthly_income}", "+$200")
    
    with col2:
        total_expenses = st.session_state.expenses['Monto'].sum()
        st.metric("💸 Gastos", f"${total_expenses}", "-$85")
    
    with col3:
        savings = st.session_state.monthly_income - total_expenses
        st.metric("💎 Ahorros", f"${savings}", f"+${st.session_state.total_saved}")
    
    with col4:
        savings_rate = (savings / st.session_state.monthly_income) * 100
        st.metric("📈 Tasa Ahorro", f"{savings_rate:.1f}%", "+3.2%")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💰 Distribución de Gastos")
        fig = px.pie(
            st.session_state.expenses,
            values='Monto',
            names='Categoría',
            color_discrete_sequence=px.colors.sequential.Purples_r
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 📈 Evolución de Ahorros")
        months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun']
        savings_evolution = [450, 520, 580, 640, 720, savings]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=months,
            y=savings_evolution,
            mode='lines+markers',
            name='Ahorros',
            line=dict(color='#10b981', width=3),
            marker=dict(size=10)
        ))
        fig.update_layout(
            title='Progreso Mensual',
            xaxis_title='Mes',
            yaxis_title='Ahorros ($)',
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Tabla de transacciones recientes
    st.markdown("### 🔄 Transacciones Recientes")
    
    transactions = pd.DataFrame({
        'Fecha': pd.date_range(end=datetime.now(), periods=10).strftime('%Y-%m-%d'),
        'Descripción': ['Supermercado', 'Netflix', 'Gasolina', 'Restaurante', 'Farmacia', 
                       'Amazon', 'Uber', 'Starbucks', 'Gimnasio', 'Electricidad'],
        'Categoría': ['Alimentación', 'Suscripciones', 'Transporte', 'Entretenimiento', 'Salud',
                     'Compras', 'Transporte', 'Alimentación', 'Suscripciones', 'Servicios'],
        'Monto': [-85.50, -15.99, -45.00, -62.30, -23.45, -127.89, -18.50, -6.75, -45.00, -89.20]
    })
    
    st.dataframe(transactions, use_container_width=True, hide_index=True)

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**🛡️ Seguridad Bancaria**")
    st.caption("Encriptación nivel bancario")

with col2:
    st.markdown("**🔒 Privacidad**")
    st.caption("Tus datos nunca se venden")

with col3:
    st.markdown("**💬 Soporte 24/7**")
    st.caption("IA siempre disponible")

st.markdown("<p style='text-align: center; color: #999; margin-top: 2rem;'>Alivia © 2025 - Tu aliado financiero IA</p>", unsafe_allow_html=True)
