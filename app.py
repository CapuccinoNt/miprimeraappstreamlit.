import streamlit as st

# Título de la app
st.title("Adivinare Cuantos años tienes!")

# Texto simple
st.write("Hola, soy akinator y adivinare tu nombre")

# Un input interactivo
nombre = st.text_input("¿Cómo te llamas?")

# Respuesta condicional
if nombre:
    st.write(f"...Te llamas: {nombre}! ¿Acerté?")

# Un botón
if st.button("Presiona aquí"):
    st.balloons()  # Animación de globos
    st.success("¡Funciona perfectamente!")
