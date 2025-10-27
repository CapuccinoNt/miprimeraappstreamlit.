import streamlit as st

# Título de la app
st.title("Te dire tu edad")

# Texto simple
st.write("Hola, te dire tu edad EXACTA")

# Un input interactivo
nombre = st.text_input("¿Cuantos años tienes?")

# Respuesta condicional
if nombre:
    st.write(f"tienes {nombre} años")


