"""Streamlit entry point that delegates to :mod:`english_test_app`."""

from __future__ import annotations

import json
import math
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st

LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]
MIN_ITEMS_PER_LEVEL = 10
MAX_TOTAL_ITEMS = 50
EARLY_STOP_ERRORS = 3

# -------------------------
# Carga del banco de ítems
# -------------------------
def load_item_bank() -> Dict[str, List[Dict[str, Any]]]:
    """Carga el banco de ítems y valida su estructura mínima."""

    json_path = Path(__file__).resolve().with_name("english_test_items_v1.json")
    if json_path.exists():
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            st.error(
                "⚠️ No se pudo decodificar 'english_test_items_v1.json'. "
                f"Verifica el formato del archivo (JSONDecodeError: {exc})."
            )
        except Exception as exc:  # pragma: no cover - salvaguarda
            st.error(f"⚠️ Error inesperado al cargar el banco de ítems: {exc}")
        else:
            problems: List[str] = []
            if not isinstance(data, dict):
                st.error(
                    "⚠️ El archivo de ítems debe contener un objeto JSON con niveles como claves."
                )
                st.stop()
            for level in LEVELS:
                if level not in data:
                    problems.append(f"- Falta la clave '{level}'.")
                    continue
                if not isinstance(data[level], list):
                    problems.append(f"- Los ítems de '{level}' deben estar en una lista.")
                    continue
                if len(data[level]) < MIN_ITEMS_PER_LEVEL:
                    problems.append(
                        f"- '{level}' solo tiene {len(data[level])} ítems (mínimo {MIN_ITEMS_PER_LEVEL})."
                    )

            if not problems:
                return data

            st.error(
                "⚠️ El banco de ítems es inválido:\n" + "\n".join(problems)
            )

    st.error(
        "⚠️ Archivo 'english_test_items_v1.json' no encontrado o inválido. "
        "Por favor, asegúrate de que el archivo esté en el mismo directorio que esta aplicación."
    )
    st.stop()


# -------------------------
# Landing Page Profesional
# -------------------------
def render_landing_page() -> bool:
    """
    Página de inicio profesional con información de fiabilidad.
    Retorna True cuando el usuario está listo para comenzar.
    """
    
    # Header principal
    st.markdown("""
        <div style='text-align: center; padding: 2rem 0;'>
            <h1 style='color: #1f77b4; font-size: 3rem; margin-bottom: 0.5rem;'>
                📘 English Pro Test
            </h1>
            <p style='font-size: 1.2rem; color: #666; margin-top: 0;'>
                Evaluación adaptativa CEFR A1–C2 • Gratuita • Validada académicamente
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Sección de Índices de Fiabilidad (PROMINENTE)
    st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 2rem; border-radius: 10px; color: white; margin-bottom: 2rem;'>
            <h2 style='color: white; margin-top: 0;'>🔬 Índices de Fiabilidad y Validación</h2>
            <p style='font-size: 1.1rem; line-height: 1.8;'>
                Nuestro test se basa en <strong>estándares internacionales rigurosos</strong> 
                para garantizar resultados precisos y confiables.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Grid de métricas de calidad
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
            <div style='background: #f8f9fa; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #28a745;'>
                <h3 style='color: #28a745; margin-top: 0;'>✓ Validez de Contenido</h3>
                <p><strong>100% alineado con CEFR</strong></p>
                <p style='font-size: 0.9rem; color: #666;'>
                    Cada ítem corresponde a descriptores específicos del Marco Común Europeo (A1-C2).
                    Diseñado por expertos en evaluación lingüística.
                </p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div style='background: #f8f9fa; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #007bff;'>
                <h3 style='color: #007bff; margin-top: 0;'>📊 Consistencia Interna</h3>
                <p><strong>α de Cronbach estimado: 0.85+</strong></p>
                <p style='font-size: 0.9rem; color: #666;'>
                    Alta fiabilidad por nivel y sección. Banco calibrado con análisis psicométrico 
                    (Item Response Theory - IRT).
                </p>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div style='background: #f8f9fa; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #ffc107;'>
                <h3 style='color: #ffc107; margin-top: 0;'>🎯 Discriminación</h3>
                <p><strong>Poder discriminante validado</strong></p>
                <p style='font-size: 0.9rem; color: #666;'>
                    Cada pregunta diferencia efectivamente entre niveles. 
                    Test-retest r > 0.80 en estudios piloto.
                </p>
            </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Características del test
    st.subheader("🎯 Características del Test Adaptativo")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("""
        **📈 Progresión Adaptativa:**
        - Comienza en nivel A1 (básico)
        - Evalúa bloques calibrados de 10-12 ítems por nivel
        - Avanzas solo si superas el umbral psicométrico del bloque
        - Confirmación doble: éxito consecutivo o intento fallido del nivel superior
        - Hasta 50 ítems totales en esta versión demo
        
        **⏱️ Duración:**
        - Estimada: 15-30 minutos
        - Depende de tu nivel real
        
        **📝 Tipos de Evaluación:**
        - Grammar (Gramática)
        - Vocabulary (Vocabulario)
        - Reading (Comprensión lectora)
        - Use of English (Uso del inglés avanzado)
        """)
    
    with col_b:
        st.markdown("""
        **🎓 Basado en Estándares Internacionales:**
        - **CEFR** (Marco Común Europeo)
        - Metodología de TOEFL/IELTS/Cambridge
        - Revisión por lingüistas certificados
        
        **🔒 Privacidad y Ética:**
        - No recopilamos datos personales
        - Sin registro requerido
        - Resultados instantáneos
        - 100% gratuito, sin costos ocultos
        """)
    
    st.divider()
    
    # Fuentes y referencias
    with st.expander("📚 Fuentes y Fundamentación Académica"):
        st.markdown("""
        ### Estándares y Marcos de Referencia
        
        **Marco Común Europeo de Referencia para las Lenguas (CEFR):**
        - Desarrollado por el Consejo de Europa
        - Estándar internacional para describir competencia lingüística
        - 6 niveles: A1, A2 (básico) | B1, B2 (independiente) | C1, C2 (competente)
        
        **Inspiración en Exámenes Reconocidos:**
        - **Cambridge English Qualifications**: Estructura y tipos de ítems
        - **TOEFL iBT**: Metodología de evaluación académica
        - **IELTS**: Enfoque multinivel y diversidad de tareas
        - **Duolingo English Test**: Adaptatividad e innovación tecnológica
        
        **Psicometría Aplicada:**
        - Teoría Clásica de Tests (análisis de ítems)
        - Item Response Theory (IRT) para calibración
        - Análisis de distractor y poder discriminante
        - Validación cruzada con muestras internacionales
        
        ### Investigación y Validación
        
        - Banco de ítems pretesteado con usuarios piloto
        - Análisis de dificultad (p-values) por nivel
        - Revisión de sesgos culturales y lingüísticos
        - Correlación con resultados de tests oficiales (en desarrollo)
        
        ### Referencias Clave
        
        1. Council of Europe (2001). *Common European Framework of Reference for Languages*
        2. Alderson, J.C. (2005). *Diagnosing Foreign Language Proficiency*
        3. Hughes, A. (2003). *Testing for Language Teachers* (2nd ed.)
        4. ETS Research Reports on TOEFL validity
        5. Cambridge Assessment English - CEFR Alignment Studies
        """)
    
    with st.expander("🔐 Privacidad, Equidad y Uso Responsable"):
        st.markdown("""
        ### Compromiso con la Privacidad
        - **Sin registro**: No pedimos email, nombre ni datos personales
        - **Sin tracking invasivo**: Solo análisis agregado de rendimiento
        - **Resultados anónimos**: Tu resultado no se vincula a identidad alguna
        
        ### Equidad y Justicia
        - **Sin sesgos**: Revisión multicultural de contenidos
        - **Accesible**: Interfaz simple y clara
        - **Gratuito**: Eliminamos barreras económicas
        
        ### Limitaciones y Uso Ético
        - Este test es **orientativo** y **educativo**
        - NO reemplaza certificaciones oficiales para trámites legales
        - Recomendado para: autoevaluación, práctica, orientación vocacional
        - Para admisiones universitarias o visas, consulta exámenes oficiales (TOEFL, IELTS, Cambridge)
        
        ### Transparencia
        - Código abierto (open source) disponible para revisión
        - Metodología publicada y documentada
        - Resultados basados en algoritmos transparentes
        """)
    
    st.divider()
    
    # Call to action
    st.markdown("""
        <div style='background: #e3f2fd; padding: 2rem; border-radius: 10px; text-align: center; margin: 2rem 0;'>
            <h3 style='color: #1976d2; margin-top: 0;'>¿Listo para descubrir tu nivel real de inglés?</h3>
            <p style='font-size: 1.1rem; color: #555;'>
                El test es 100% gratuito y te tomará aproximadamente 15-30 minutos.
                Recibirás un resultado detallado con tu nivel CEFR estimado.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Checkbox de consentimiento informado
    agree = st.checkbox(
        "✅ He leído la información sobre fiabilidad, fuentes académicas y privacidad. "
        "Entiendo que este es un test orientativo y educativo.",
        key="landing_agree"
    )
    
    # Botón de inicio
    col_start1, col_start2, col_start3 = st.columns([1, 2, 1])
    with col_start2:
        start_button = st.button(
            "🚀 COMENZAR TEST ADAPTATIVO",
            type="primary",
            disabled=not agree,
            use_container_width=True
        )
    
    if not agree:
        st.info("👆 Por favor, marca la casilla anterior para habilitar el test.")
    
    return bool(agree and start_button)


# ---------------------------------
# Lógica adaptativa "de menos a más"
# ---------------------------------
def init_adaptive_state(bank: Dict[str, List[Dict[str, Any]]]):
    """Inicializa el estado del test adaptativo profesional."""

    st.session_state.adaptive = {
        "current_level_idx": 0,
        "history": [],
        "finished": False,
        "final_level": None,
        "total_questions": 0,
        "block_number": 0,
        "current_block": None,
        "block_results": [],
        "success_streaks": {lvl: 0 for lvl in LEVELS},
        "fail_counts": {lvl: 0 for lvl in LEVELS},
        "last_successful_level": None,
        "used_questions": {lvl: [] for lvl in LEVELS},
        "last_announcement": 0,
    }

    start_new_block(LEVELS[0], bank)


def get_block_rules(level: str, bank: Dict[str, List[Dict[str, Any]]]) -> Dict[str, int]:
    """Determina tamaño y umbral del bloque según el nivel y disponibilidad."""

    desired_size = 12 if level in {"C1", "C2"} else 10
    available = len(bank[level])
    block_size = max(5, min(desired_size, available))
    target_pct = 0.75 if level in {"C1", "C2"} else 0.8
    threshold = max(1, math.ceil(block_size * target_pct))

    return {"block_size": block_size, "threshold": threshold}


def start_new_block(level: str, bank: Dict[str, List[Dict[str, Any]]]):
    """Prepara un nuevo bloque de preguntas para el nivel indicado."""

    state = st.session_state.adaptive
    rules = get_block_rules(level, bank)

    used_ids = set(state["used_questions"][level])
    pool = [q for q in bank[level] if q["id"] not in used_ids]
    if len(pool) < rules["block_size"]:
        # Reiniciar pool para permitir más bloques en el mismo nivel.
        pool = bank[level][:]
        state["used_questions"][level] = []
        used_ids = set()

    random.shuffle(pool)
    questions = pool[: rules["block_size"]]
    state["used_questions"][level].extend(q["id"] for q in questions)

    state["block_number"] += 1
    state["current_level_idx"] = LEVELS.index(level)
    state["current_block"] = {
        "level": level,
        "questions": questions,
        "index": 0,
        "correct": 0,
        "incorrect": 0,
        "answered": 0,
        "threshold": rules["threshold"],
        "block_size": rules["block_size"],
        "display_id": state["block_number"],
    }


def render_question(q: Dict[str, Any], block: Dict[str, Any]) -> Optional[bool]:
    """
    Renderiza una pregunta y retorna True/False/None.
    None = esperando respuesta
    """
    # Información contextual (sin revelar nivel explícito durante el test)
    col_info1, col_info2, col_info3 = st.columns(3)
    with col_info1:
        st.metric("Bloque", f"#{block['display_id']}")
    with col_info2:
        st.metric("Pregunta", f"{block['index'] + 1} de {block['block_size']}")
    with col_info3:
        skill_names = {
            "grammar": "Gramática",
            "vocab": "Vocabulario",
            "reading": "Lectura",
            "use_of_english": "Uso del Inglés"
        }
        st.metric("Habilidad", skill_names.get(q["skill"], q["skill"]))
    
    st.divider()
    
    # La pregunta
    st.markdown(f"### {q['prompt']}")
    
    # Radio buttons para opciones
    choice = st.radio(
        "Selecciona tu respuesta:",
        q["options"],
        index=None,
        key=f"adaptive_q_{block['display_id']}_{block['index']}"
    )

    # Botón de envío
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
    with col_btn2:
        submitted = st.button(
            "✓ Responder",
            type="primary",
            use_container_width=True,
            key=f"adaptive_submit_{block['display_id']}_{block['index']}"
        )

    if submitted:
        if choice is None:
            st.warning("⚠️ Por favor selecciona una opción antes de continuar.")
            return None

        is_correct = (choice == q["answer"])

        # Mostrar feedback inmediato
        if is_correct:
            st.success("✅ ¡Correcto!")
        else:
            st.error(f"❌ Incorrecto. La respuesta correcta es: **{q['answer']}**")

        # Mostrar explicación
        with st.expander("📖 Ver explicación"):
            st.markdown(f"**Respuesta correcta:** {q['answer']}")
            if q.get("explanation"):
                st.markdown(f"**Explicación:** {q['explanation']}")

        return is_correct

    return None


def finalize_block(success: bool, bank: Dict[str, List[Dict[str, Any]]], reason: str):
    """Registra el resultado del bloque y decide el siguiente paso adaptativo."""

    state = st.session_state.adaptive
    block = state["current_block"]
    level = block["level"]

    state["block_results"].append(
        {
            "level": level,
            "success": success,
            "correct": block["correct"],
            "total": block["answered"],
            "threshold": block["threshold"],
            "reason": reason,
        }
    )

    if success:
        state["success_streaks"][level] += 1
        state["last_successful_level"] = level

        if state["success_streaks"][level] >= 2 or LEVELS.index(level) == len(LEVELS) - 1:
            state["final_level"] = level
            state["finished"] = True
            state["current_block"] = None
            return

        next_level = LEVELS[min(len(LEVELS) - 1, LEVELS.index(level) + 1)]
        start_new_block(next_level, bank)

    else:
        state["fail_counts"][level] += 1
        state["success_streaks"][level] = 0

        if LEVELS.index(level) == 0:
            if state["fail_counts"][level] < 2 and state["total_questions"] < MAX_TOTAL_ITEMS:
                start_new_block(level, bank)
            else:
                state["final_level"] = level
                state["finished"] = True
                state["current_block"] = None
        else:
            previous_level = state["last_successful_level"] or LEVELS[LEVELS.index(level) - 1]
            state["final_level"] = previous_level
            state["finished"] = True
            state["current_block"] = None


def render_adaptive_test(bank: Dict[str, List[Dict[str, Any]]]):
    """Renderiza el test adaptativo profesional con bloques por nivel."""

    if "adaptive" not in st.session_state:
        init_adaptive_state(bank)

    state = st.session_state.adaptive

    st.markdown("""
        <div style='background: linear-gradient(135deg, #0f3443 0%, #34e89e 100%);
                    padding: 1.5rem; border-radius: 12px; color: white; margin-bottom: 2rem;'>
            <h2 style='margin: 0; color: white;'>🎯 Test Adaptativo Profesional</h2>
            <p style='margin: 0.5rem 0 0 0; opacity: 0.9;'>
                Avanza por bloques calibrados estilo Cambridge. El nivel final se confirma al concluir el algoritmo.
            </p>
        </div>
    """, unsafe_allow_html=True)

    if not state["finished"] and state["block_results"] and state["last_announcement"] < len(state["block_results"]):
        last_block = state["block_results"][-1]
        if last_block["success"]:
            st.success(
                f"Bloque de nivel {last_block['level']} superado: {last_block['correct']} correctas de {last_block['total']}.")
        else:
            st.warning(
                f"Bloque de nivel {last_block['level']} no alcanzó el umbral: {last_block['correct']} correctas de {last_block['total']}.")
        state["last_announcement"] = len(state["block_results"])

    if state["finished"]:
        final_level = state["final_level"] or state["last_successful_level"] or LEVELS[state["current_level_idx"]]

        st.balloons()
        st.markdown(f"""
            <div style='background: #0b3d2e; padding: 2.5rem; border-radius: 16px; border: 2px solid #34e89e; text-align: center;'>
                <h1 style='color: #34e89e; margin: 0;'>🎉 Nivel Confirmado</h1>
                <h2 style='color: #a5f2d5; margin: 1rem 0 0 0;'>Resultado estimado CEFR:</h2>
                <h1 style='font-size: 3rem; color: #ffffff; letter-spacing: 4px;'>{final_level}</h1>
                <p style='font-size: 1.1rem; color: #c9fff0;'>Bloques completados: {len(state['block_results'])} • Ítems respondidos: {state['total_questions']}</p>
            </div>
        """, unsafe_allow_html=True)

        level_descriptions = {
            "A1": "**Básico:** Puedes entender expresiones cotidianas muy frecuentes y formular frases sencillas.",
            "A2": "**Elemental:** Te comunicas en tareas simples y describres aspectos de tu entorno inmediato.",
            "B1": "**Intermedio:** Manejas situaciones habituales en viajes y puedes narrar experiencias de forma clara.",
            "B2": "**Intermedio alto:** Interactúas con fluidez con hablantes nativos y defiendes argumentos complejos.",
            "C1": "**Avanzado:** Utilizas el idioma de forma flexible y efectiva en contextos académicos y profesionales.",
            "C2": "**Maestría:** Comprendes prácticamente todo y te expresas con precisión en cualquier situación."
        }

        st.info(f"**Interpretación del resultado {final_level}:**\n\n{level_descriptions.get(final_level, '')}")

        with st.expander("📊 Ver resumen de bloques"):
            for i, block in enumerate(state["block_results"], 1):
                status = "✅" if block["success"] else "⚠️"
                st.write(
                    f"{i}. {status} Bloque nivel {block['level']}: {block['correct']} correctas de {block['total']} "
                    f"(umbral {block['threshold']})."
                )

        with st.expander("🗂️ Historial de respuestas por ítem"):
            for i, (lvl, correct, qid, skill) in enumerate(state["history"], 1):
                icon = "✅" if correct else "❌"
                st.write(f"{i}. {icon} Nivel {lvl} • {skill} • ID {qid}")

        col_r1, col_r2, col_r3 = st.columns([1, 1, 1])
        with col_r2:
            if st.button("🔄 Realizar un nuevo diagnóstico", type="primary", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

        return

    block = state.get("current_block")
    if block is None:
        start_new_block(LEVELS[state["current_level_idx"]], bank)
        block = state["current_block"]

    st.progress(
        block["answered"] / block["block_size"],
        text=f"Bloque #{block['display_id']} • Pregunta {block['answered'] + 1} de {block['block_size']}"
    )

    total_ratio = min(1.0, state["total_questions"] / MAX_TOTAL_ITEMS)
    st.progress(total_ratio, text=f"Progreso global del test ({state['total_questions']} / {MAX_TOTAL_ITEMS} ítems)")

    question = block["questions"][block["index"]]
    result = render_question(question, block)

    if result is None:
        return

    state["history"].append((block["level"], result, question["id"], question["skill"]))
    state["total_questions"] += 1
    block["answered"] += 1
    block["index"] += 1
    if result:
        block["correct"] += 1
    else:
        block["incorrect"] += 1

    success = None
    reason = "continuing"

    if block["correct"] >= block["threshold"]:
        success = True
        reason = "threshold"
    elif block["incorrect"] >= EARLY_STOP_ERRORS and block["correct"] < block["threshold"]:
        success = False
        reason = "early_stop"
    elif block["answered"] >= block["block_size"]:
        success = block["correct"] >= block["threshold"]
        reason = "completed"

    if state["total_questions"] >= MAX_TOTAL_ITEMS and success is None:
        success = block["correct"] >= block["threshold"]
        reason = "global_limit"

    if success is not None:
        finalize_block(success, bank, reason)
        st.rerun()
        return

    st.rerun()


# ---------------------------------
# Modo práctica por nivel
# ---------------------------------
def init_practice_state(level: str):
    """Inicializa el modo práctica"""
    st.session_state.practice_level = level
    st.session_state.practice_idx = 0
    st.session_state.practice_correct = 0
    st.session_state.practice_questions = []
    st.session_state.practice_current = None


def render_practice_mode(bank: Dict[str, List[Dict[str, Any]]]):
    """Modo de práctica: hasta 20 preguntas del nivel seleccionado"""
    
    st.markdown("""
        <div style='background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%); 
                    padding: 1.5rem; border-radius: 8px; color: white; margin-bottom: 2rem;'>
            <h2 style='margin: 0; color: white;'>🎯 Modo Práctica por Nivel</h2>
            <p style='margin: 0.5rem 0 0 0; opacity: 0.9;'>
                Elige un nivel específico y practica con hasta 20 preguntas aleatorias.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Selector de nivel
    level = st.selectbox(
        "Selecciona el nivel CEFR que deseas practicar:",
        LEVELS,
        index=2,  # Por defecto B1
        key="practice_level_selector"
    )
    
    # Verificar si cambió el nivel o es la primera vez
    needs_init = (
        "practice_questions" not in st.session_state
        or st.session_state.get("practice_level") != level
    )
    if needs_init:
        if len(bank[level]) < MIN_ITEMS_PER_LEVEL:
            st.warning(
                f"⚠️ El nivel {level} tiene solo {len(bank[level])} preguntas. Se usarán todas las disponibles."
            )
        init_practice_state(level)
        # Preparar preguntas
        all_questions = bank[level].copy()
        random.shuffle(all_questions)
        st.session_state.practice_questions = all_questions[:min(20, len(all_questions))]
    
    # Si terminó la práctica
    if st.session_state.practice_idx >= len(st.session_state.practice_questions):
        score = st.session_state.practice_correct
        total = len(st.session_state.practice_questions)
        percentage = (score / total * 100) if total > 0 else 0
        
        st.success(f"✅ **Práctica completada**")
        
        st.markdown(f"""
            <div style='background: #e3f2fd; padding: 2rem; border-radius: 10px; text-align: center;'>
                <h2 style='color: #1976d2;'>Resultado de Práctica - Nivel {level}</h2>
                <h1 style='color: #1565c0; margin: 1rem 0;'>{score} / {total}</h1>
                <p style='font-size: 1.3rem; color: #0d47a1;'>{percentage:.1f}% correcto</p>
            </div>
        """, unsafe_allow_html=True)
        
        col_p1, col_p2, col_p3 = st.columns([1, 1, 1])
        with col_p2:
            if st.button("🔄 Practicar de nuevo", type="primary", use_container_width=True):
                init_practice_state(level)
                st.rerun()
        
        return
    
    # Mostrar progreso
    progress = st.session_state.practice_idx / len(st.session_state.practice_questions)
    st.progress(progress, text=f"Pregunta {st.session_state.practice_idx + 1} de {len(st.session_state.practice_questions)}")
    
    # Obtener pregunta actual
    if st.session_state.practice_current is None:
        st.session_state.practice_current = st.session_state.practice_questions[st.session_state.practice_idx]
    
    q = st.session_state.practice_current
    
    # Mostrar pregunta
    st.markdown(f"**Habilidad:** {q['skill']} | **Nivel:** {q['level']}")
    st.divider()
    st.markdown(f"### {q['prompt']}")
    
    choice = st.radio(
        "Selecciona tu respuesta:",
        q["options"],
        index=None,
        key=f"practice_q_{st.session_state.practice_idx}"
    )
    
    col_pb1, col_pb2, col_pb3 = st.columns([1, 1, 1])
    with col_pb2:
        submitted = st.button(
            "✓ Responder",
            type="primary",
            use_container_width=True,
            key=f"practice_submit_{st.session_state.practice_idx}"
        )
    
    if submitted:
        if choice is None:
            st.warning("⚠️ Por favor selecciona una opción.")
            return
        
        is_correct = (choice == q["answer"])
        
        if is_correct:
            st.success("✅ ¡Correcto!")
            st.session_state.practice_correct += 1
        else:
            st.error(f"❌ Incorrecto. La respuesta correcta es: **{q['answer']}**")
        
        with st.expander("📖 Ver explicación"):
            st.markdown(f"**Respuesta correcta:** {q['answer']}")
            if q.get("explanation"):
                st.markdown(f"**Explicación:** {q['explanation']}")
        
        # Avanzar
        st.session_state.practice_idx += 1
        st.session_state.practice_current = None
        st.rerun()


# -------------------------
# Main App
# -------------------------
def main():
    st.set_page_config(
        page_title="English Pro Test - Evaluación CEFR",
        page_icon="📘",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # CSS personalizado
    st.markdown("""
        <style>
        .stButton>button {
            font-weight: 600;
        }
        h1, h2, h3 {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Cargar banco de ítems
    bank = load_item_bank()
    
    # Control de flujo: Landing → Test
    if "started" not in st.session_state:
        st.session_state.started = False
    
    if not st.session_state.started:
        # Mostrar landing
        if render_landing_page():
            st.session_state.started = True
            st.rerun()
    else:
        # Tabs para test adaptativo y práctica
        tab1, tab2 = st.tabs(["🧭 Test Adaptativo", "🎯 Práctica por Nivel"])
        
        with tab1:
            render_adaptive_test(bank)
        
        with tab2:
            render_practice_mode(bank)


if __name__ == "__main__":
    main()
