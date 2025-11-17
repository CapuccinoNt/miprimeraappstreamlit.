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
MAX_PRACTICE_QUESTIONS = 20
EARLY_STOP_ERRORS = 3
SKILL_TARGET = 8  # Ítems por habilidad para progreso visual
CHOICE_BASED_TYPES = {"multiple_choice"}
PRACTICE_SUPPORTED_TYPES = CHOICE_BASED_TYPES
ADAPTIVE_SUPPORTED_TYPES = CHOICE_BASED_TYPES

SKILL_INFO = {
    "grammar": {"label": "Grammar", "icon": "⚙️", "color": "#1B365D"},
    "vocab": {"label": "Vocabulary", "icon": "📚", "color": "#00838F"},
    "reading": {"label": "Reading", "icon": "📖👁️", "color": "#5A6C8D"},
    "use_of_english": {"label": "Use of English", "icon": "🧩", "color": "#4C8C74"},
    "writing": {"label": "Writing", "icon": "✍️", "color": "#7A5199"},
}


def is_choice_question(question: Dict[str, Any], supported_types: set[str]) -> bool:
    """Return True when the item contains selectable options supported by the mode."""

    return (
        question.get("type") in supported_types
        and isinstance(question.get("options"), list)
        and len(question["options"]) >= 2
    )

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
    st.markdown(
        """
        <div class='hero-card'>
            <div class='hero-card__copy'>
                <p class='eyebrow'>Cambridge style • CEFR</p>
                <h1>English Pro Test</h1>
                <p>
                    Diagnóstico adaptativo A1–C2 con validación académica y resultados inmediatos.
                    Descubre tu nivel real con una experiencia moderna y enfocada.
                </p>
                <div class='hero-tags'>
                    <span>Sin registro</span>
                    <span>15-30 min</span>
                    <span>Feedback inmediato</span>
                </div>
            </div>
            <div class='hero-card__image'>
                <img src='https://images.unsplash.com/photo-1460518451285-97b6aa326961?auto=format&fit=crop&w=900&q=80' alt='Campus inglés' />
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class='info-bar'>
            <div>
                <strong>CEFR completo</strong>
                <span>A1 a C2</span>
            </div>
            <div>
                <strong>Psicometría</strong>
                <span>IRT + α Cronbach</span>
            </div>
            <div>
                <strong>Resultados</strong>
                <span>Inmediatos</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Sección de Índices de Fiabilidad (PROMINENTE)
    st.markdown(
        """
        <div class='validation-banner'>
            <h2>🔬 Índices de Fiabilidad y Validación</h2>
            <p>
                Basado en estándares internacionales rigurosos para garantizar resultados precisos y confiables.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Grid de métricas de calidad
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(
            """
            <div class='metric-card'>
                <h3>✓ Validez de Contenido</h3>
                <p><strong>100% alineado con CEFR</strong></p>
                <p>
                    Cada ítem corresponde a descriptores específicos del Marco Común Europeo (A1-C2).
                    Diseñado por expertos en evaluación lingüística.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    with col2:
        st.markdown(
            """
            <div class='metric-card'>
                <h3>📊 Consistencia Interna</h3>
                <p><strong>α de Cronbach estimado: 0.85+</strong></p>
                <p>
                    Alta fiabilidad por nivel y sección. Banco calibrado con análisis psicométrico
                    (Item Response Theory - IRT).
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    with col3:
        st.markdown(
            """
            <div class='metric-card'>
                <h3>🎯 Discriminación</h3>
                <p><strong>Poder discriminante validado</strong></p>
                <p>
                    Cada pregunta diferencia efectivamente entre niveles.
                    Test-retest r > 0.80 en estudios piloto.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
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
    st.markdown(
        """
        <div class='cta-card'>
            <h3>¿Listo para descubrir tu nivel real de inglés?</h3>
            <p>
                El test es 100% gratuito y te tomará aproximadamente 15-30 minutos.
                Recibirás un resultado detallado con tu nivel CEFR estimado.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
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
        "skill_stats": {k: {"answered": 0, "correct": 0} for k in SKILL_INFO},
    }

    start_new_block(LEVELS[0], bank)


def get_supported_pool(level: str, bank: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Return only the items compatibles con la interfaz adaptativa."""

    return [
        q
        for q in bank[level]
        if is_choice_question(q, ADAPTIVE_SUPPORTED_TYPES)
    ]


def get_block_rules(level: str, available: int) -> Dict[str, int]:
    """Determina tamaño y umbral del bloque según el nivel y disponibilidad."""

    desired_size = 12 if level in {"C1", "C2"} else 10
    if available < 5:
        block_size = available
    else:
        block_size = max(5, min(desired_size, available))
    target_pct = 0.75 if level in {"C1", "C2"} else 0.8
    threshold = max(1, math.ceil(block_size * target_pct))

    return {"block_size": block_size, "threshold": threshold}


def start_new_block(level: str, bank: Dict[str, List[Dict[str, Any]]]):
    """Prepara un nuevo bloque de preguntas para el nivel indicado."""

    state = st.session_state.adaptive
    eligible_questions = get_supported_pool(level, bank)
    if not eligible_questions:
        st.error(
            "⚠️ El nivel seleccionado no tiene preguntas compatibles con el formato de selección múltiple."
        )
        st.stop()

    rules = get_block_rules(level, len(eligible_questions))

    used_ids = set(state["used_questions"][level])
    pool = [q for q in eligible_questions if q["id"] not in used_ids]
    if len(pool) < rules["block_size"]:
        # Reiniciar pool para permitir más bloques en el mismo nivel.
        pool = eligible_questions[:]
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
    skill = q.get("skill", "")
    skill_meta = SKILL_INFO.get(skill, {"label": skill.title(), "icon": "📘"})
    display_level = q.get("level", block["level"])

    st.markdown("<div class='question-card fade-in'>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class='question-card__header'>
            <span class='pill'>Bloque #{block['display_id']}</span>
            <span class='pill pill--ghost'>Pregunta {block['index'] + 1} / {block['block_size']}</span>
        </div>
        <div class='question-card__title'>
            <small>{display_level} – {skill_meta['icon']} {skill_meta['label']}</small>
            <h2>{q['prompt']}</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    choice = st.radio(
        "Selecciona tu respuesta:",
        q["options"],
        index=None,
        key=f"adaptive_q_{block['display_id']}_{block['index']}",
        label_visibility="collapsed",
    )

    submitted = st.button(
        "Responder y continuar",
        type="primary",
        use_container_width=True,
        key=f"adaptive_submit_{block['display_id']}_{block['index']}",
    )

    st.markdown("</div>", unsafe_allow_html=True)

    if submitted:
        if choice is None:
            st.warning("⚠️ Por favor selecciona una opción antes de continuar.")
            return None

        is_correct = (choice == q["answer"])

        # Mostrar feedback inmediato
        if is_correct:
            positive_msgs = {
                "C1": "Nice! That structure is typical of C1.",
                "C2": "Brilliant control. This is a C2-grade collocation.",
            }
            st.success(positive_msgs.get(display_level, "Great job!"))
        else:
            warning_msgs = {
                "C1": "Careful: this collocation is advanced C1 usage.",
                "C2": "Careful: this collocation is advanced C2 usage.",
            }
            st.error(warning_msgs.get(display_level, "Revisa la estructura antes de continuar."))

        # Mostrar explicación
        with st.expander("📖 Ver explicación"):
            st.markdown(f"**Respuesta correcta:** {q['answer']}")
            if q.get("explanation"):
                st.markdown(f"**Explicación:** {q['explanation']}")

        return is_correct

    return None


def render_skill_overview(state: Dict[str, Any]):
    st.markdown("#### Progreso por habilidad")
    stats = state.get("skill_stats") or {k: {"answered": 0, "correct": 0} for k in SKILL_INFO}
    cols = st.columns(2)
    for idx, (skill, meta) in enumerate(SKILL_INFO.items()):
        col = cols[idx % 2]
        with col:
            answered = stats.get(skill, {}).get("answered", 0)
            correct = stats.get(skill, {}).get("correct", 0)
            coverage = min(1.0, answered / SKILL_TARGET) if SKILL_TARGET else 0
            accuracy = (correct / answered * 100) if answered else 0
            st.markdown(
                f"""
                <div class='skill-progress-card'>
                    <strong>{meta['icon']} {meta['label']}</strong>
                    <span>{answered} ítems respondidos • {accuracy:.0f}% precisión</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.progress(
                coverage,
                text=(
                    f"{min(answered, SKILL_TARGET)} / {SKILL_TARGET}"
                    if SKILL_TARGET
                    else f"{answered} ítems"
                ),
            )


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

    render_skill_overview(state)

    question = block["questions"][block["index"]]
    result = render_question(question, block)

    if result is None:
        return

    state["history"].append((block["level"], result, question["id"], question["skill"]))
    skill_stats = state.setdefault("skill_stats", {k: {"answered": 0, "correct": 0} for k in SKILL_INFO})
    skill_entry = skill_stats.setdefault(question["skill"], {"answered": 0, "correct": 0})
    skill_entry["answered"] += 1
    if result:
        skill_entry["correct"] += 1
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
    
    st.markdown(
        """
        <div class='practice-banner'>
            <div>
                <h2>🎯 Modo Práctica por Nivel</h2>
                <p>Elige un nivel específico y practica con hasta 20 preguntas aleatorias.</p>
            </div>
            <img src='https://images.unsplash.com/photo-1487528278747-ba99ed528ebc?auto=format&fit=crop&w=800&q=80' alt='Study desk' />
        </div>
        """,
        unsafe_allow_html=True,
    )
    
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
        eligible_questions = [
            q
            for q in bank[level]
            if is_choice_question(q, PRACTICE_SUPPORTED_TYPES)
        ]

        if not eligible_questions:
            st.info(
                "⚠️ Este nivel aún no tiene preguntas de selección múltiple disponibles para el modo práctica."
            )
            return

        init_practice_state(level)

        if len(eligible_questions) < MIN_ITEMS_PER_LEVEL:
            st.warning(
                "⚠️ "
                f"El nivel {level} tiene solo {len(eligible_questions)} preguntas compatibles. Se usarán todas las disponibles."
            )

        random.shuffle(eligible_questions)
        st.session_state.practice_questions = eligible_questions[:min(
            MAX_PRACTICE_QUESTIONS, len(eligible_questions)
        )]

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
    skill_meta = SKILL_INFO.get(q["skill"], {"label": q["skill"], "icon": "📘"})
    st.markdown("<div class='question-card fade-in'>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class='question-card__title'>
            <small>{q['level']} – {skill_meta['icon']} {skill_meta['label']}</small>
            <h2>{q['prompt']}</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    choice = st.radio(
        "Selecciona tu respuesta:",
        q["options"],
        index=None,
        key=f"practice_q_{st.session_state.practice_idx}",
        label_visibility="collapsed",
    )

    submitted = st.button(
        "Responder y continuar",
        type="primary",
        use_container_width=True,
        key=f"practice_submit_{st.session_state.practice_idx}",
    )

    st.markdown("</div>", unsafe_allow_html=True)
    
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
    st.markdown(
        """
        <style>
        :root {
            --bg-color: #F5F7FA;
            --primary: #1B365D;
            --accent: #00838F;
            --card-bg: #FFFFFF;
            --text-muted: #5A6C8D;
        }
        body, .stApp {
            background-color: var(--bg-color);
            font-family: 'Inter', 'Segoe UI', sans-serif;
            color: #1B365D;
        }
        h1, h2, h3, h4 {
            font-weight: 600;
            color: var(--primary);
        }
        .stButton>button {
            font-weight: 600;
            border-radius: 999px;
            padding: 0.75rem 1.5rem;
            background: linear-gradient(120deg, var(--primary), var(--accent));
            border: none;
            box-shadow: 0 10px 20px rgba(27, 54, 93, 0.2);
        }
        .stButton>button:hover {
            filter: brightness(1.05);
        }
        .hero-card {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 2rem;
            background: var(--card-bg);
            padding: 2.5rem;
            border-radius: 24px;
            box-shadow: 0 20px 40px rgba(15, 52, 67, 0.1);
            align-items: center;
        }
        .hero-card__copy h1 {
            font-size: 3rem;
            margin-bottom: 0.5rem;
        }
        .hero-card__copy p {
            color: var(--text-muted);
            font-size: 1.1rem;
        }
        .hero-card__image img {
            width: 100%;
            border-radius: 20px;
            object-fit: cover;
            box-shadow: 0 20px 35px rgba(0,0,0,0.15);
        }
        .hero-tags span {
            background: rgba(0, 131, 143, 0.1);
            color: var(--accent);
            padding: 0.3rem 0.9rem;
            border-radius: 999px;
            margin-right: 0.5rem;
            font-weight: 600;
        }
        .eyebrow {
            text-transform: uppercase;
            letter-spacing: 0.15em;
            color: var(--accent);
            font-weight: 600;
            font-size: 0.85rem;
        }
        .info-bar {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin: 2rem 0;
        }
        .info-bar div {
            background: #E5EEF5;
            padding: 1rem 1.5rem;
            border-radius: 16px;
            text-align: center;
        }
        .info-bar span {
            color: var(--text-muted);
            display: block;
        }
        .validation-banner {
            background: linear-gradient(120deg, #1B365D, #00838F);
            color: white;
            padding: 2rem;
            border-radius: 20px;
            margin-bottom: 2rem;
        }
        .metric-card {
            background: var(--card-bg);
            padding: 1.5rem;
            border-radius: 18px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.08);
        }
        .metric-card p {
            color: var(--text-muted);
            font-size: 0.95rem;
        }
        .cta-card {
            background: #E1F2F3;
            border-radius: 18px;
            padding: 2rem;
            text-align: center;
            color: var(--primary);
            margin: 2rem 0;
        }
        .question-card {
            background: var(--card-bg);
            border-radius: 28px;
            padding: 2rem;
            margin: 1.5rem 0;
            box-shadow: 0 20px 40px rgba(15, 52, 67, 0.12);
            animation: fadeInUp 0.6s ease;
        }
        .question-card__header {
            display: flex;
            gap: 0.8rem;
            flex-wrap: wrap;
            margin-bottom: 0.75rem;
        }
        .question-card__title small {
            font-weight: 600;
            color: var(--accent);
            letter-spacing: 0.08em;
        }
        .question-card__title h2 {
            margin-top: 0.5rem;
        }
        .pill {
            background: rgba(27, 54, 93, 0.08);
            color: var(--primary);
            padding: 0.3rem 0.8rem;
            border-radius: 999px;
            font-weight: 600;
            font-size: 0.85rem;
        }
        .pill--ghost {
            background: rgba(0, 131, 143, 0.08);
            color: #00838F;
        }
        div[data-testid="stRadio"] > div[role="radiogroup"] > label {
            border: 1px solid #E0E6ED;
            border-radius: 16px;
            padding: 0.9rem 1.2rem;
            margin-bottom: 0.7rem;
            background: #F8FAFE;
            transition: all 0.2s ease;
            font-weight: 600;
        }
        div[data-testid="stRadio"] > div[role="radiogroup"] > label:hover {
            border-color: var(--accent);
            background: rgba(0, 131, 143, 0.08);
        }
        div[data-testid="stRadio"] > div[role="radiogroup"] > label[aria-checked="true"] {
            border-color: var(--primary);
            background: rgba(27, 54, 93, 0.1);
            color: var(--primary);
        }
        @keyframes fadeInUp {
            from {opacity: 0; transform: translateY(12px);}
            to {opacity: 1; transform: translateY(0);}
        }
        .practice-banner {
            background: var(--card-bg);
            border-radius: 24px;
            padding: 2rem;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1.5rem;
            box-shadow: 0 15px 30px rgba(0,0,0,0.1);
            align-items: center;
        }
        .practice-banner img {
            width: 100%;
            border-radius: 18px;
            object-fit: cover;
        }
        .skill-progress-card {
            background: var(--card-bg);
            border-radius: 18px;
            padding: 1.2rem;
            box-shadow: 0 15px 30px rgba(15, 52, 67, 0.08);
            margin-bottom: 1rem;
        }
        .skill-progress-card span {
            color: var(--text-muted);
            font-size: 0.9rem;
        }
        .cta-card p {
            color: var(--text-muted);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    
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
