import streamlit as st


def keep(key, default, options=None, bounds=None):
    value = st.session_state.get(key, default)
    if bounds is not None:
        lo, hi = bounds
        try:
            a, b = max(lo, value[0]), min(hi, value[1])
            value = (a, b) if a <= b else default
        except (TypeError, IndexError):
            value = default
    elif options is not None:
        opts = list(options)
        if isinstance(default, list):
            value = [v for v in (value or []) if v in opts]
        elif value not in opts:
            value = default if default in opts else (opts[0] if opts else None)
    st.session_state[key] = value
    st.session_state[f"_{key}"] = value
    return f"_{key}"


def save(key):
    st.session_state[key] = st.session_state[f"_{key}"]


def save_many(keys):
    for k in keys:
        save(k)
