import io
import json
import shutil
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Literal, Optional

import hashlib

import pandas as pd
import streamlit as st

try:  # Python 3.11+
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]


SUPPORTED_UPLOADS = {".zip", ".mrpack"}
CONFIG_DIR_NAMES = ["config", "defaultconfigs", "serverconfig"]
DATA_PACK_DIR = "datapacks"
RESOURCE_PACK_DIR = "resourcepacks"
SHADER_PACK_DIR = "shaderpacks"

LOADER_FAMILIES = {
    "forge": {"forge", "neoforge"},
    "neoforge": {"forge", "neoforge"},
    "fabric": {"fabric", "quilt"},
    "quilt": {"fabric", "quilt"},
}


@dataclass
class Dep:
    modid: str
    version_range: Optional[str] = None
    required: bool = True


@dataclass
class Mod:
    id: str
    name: str
    filename: str
    path: Path
    version: Optional[str]
    loader: Optional[str]
    enabled: bool = True
    hashes: Dict[str, str] = field(default_factory=dict)
    dependencies: List[Dep] = field(default_factory=list)
    incompatibilities: List[str] = field(default_factory=list)
    source: Literal["curseforge", "modrinth", "manual"] = "manual"


@dataclass
class ConfigFile:
    path: Path
    relative_path: Path
    format: str
    original_content: str
    content: str


@dataclass
class Manifests:
    curseforge: Optional[Dict] = None
    modrinth: Optional[Dict] = None
    packwiz: Optional[Dict] = None


@dataclass
class ValidationResult:
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class Pack:
    name: str
    mc_version: Optional[str]
    loader: Optional[str]
    working_root: Path
    immutable_root: Path
    manifests: Manifests
    mods: List[Mod]
    configs: List[ConfigFile]
    datapacks: List[Path] = field(default_factory=list)
    resourcepacks: List[Path] = field(default_factory=list)
    shaderpacks: List[Path] = field(default_factory=list)
    validation: ValidationResult = field(default_factory=ValidationResult)


def get_temp_workspace() -> Path:
    workspace = Path(st.session_state.get("workspace_dir", Path.cwd() / ".app_workspace"))
    workspace.mkdir(exist_ok=True)
    st.session_state.workspace_dir = str(workspace)
    return workspace


def save_upload(upload, workspace: Path) -> Path:
    dest = workspace / upload.name
    dest.write_bytes(upload.getbuffer())
    return dest


def extract_upload(archive: Path, workspace: Path) -> Path:
    extract_root = workspace / "extracted"
    if extract_root.exists():
        shutil.rmtree(extract_root)
    extract_root.mkdir()
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(extract_root)
    inner_items = list(extract_root.iterdir())
    if len(inner_items) == 1 and inner_items[0].is_dir():
        return inner_items[0]
    return extract_root


def detect_loader_from_mods(mods: List[Mod]) -> Optional[str]:
    loaders = {m.loader for m in mods if m.loader}
    if not loaders:
        return None
    if len(loaders) == 1:
        return loaders.pop()
    return ", ".join(sorted(loaders))


def parse_manifest(root: Path) -> Manifests:
    manifests = Manifests()
    curseforge_manifest = root / "manifest.json"
    if curseforge_manifest.exists():
        manifests.curseforge = json.loads(curseforge_manifest.read_text())
    modrinth_manifest = root / "modrinth.index.json"
    if modrinth_manifest.exists():
        manifests.modrinth = json.loads(modrinth_manifest.read_text())
    packwiz_manifest = root / "pack.toml"
    if not packwiz_manifest.exists():
        packwiz_manifest = root / "packwiz.toml"
    if packwiz_manifest.exists():
        manifests.packwiz = tomllib.loads(packwiz_manifest.read_text())
    return manifests


def detect_mc_version(manifests: Manifests) -> Optional[str]:
    if manifests.curseforge:
        return manifests.curseforge.get("minecraft", {}).get("version")
    if manifests.modrinth:
        return manifests.modrinth.get("game", {}).get("version") or manifests.modrinth.get("game_version")
    if manifests.packwiz:
        return manifests.packwiz.get("versions", {}).get("minecraft")
    return None


def detect_loader(manifests: Manifests, mods: List[Mod]) -> Optional[str]:
    if manifests.curseforge:
        mod_loaders = manifests.curseforge.get("minecraft", {}).get("modLoaders", [])
        if mod_loaders:
            return mod_loaders[0].get("id")
    if manifests.modrinth:
        loaders = manifests.modrinth.get("dependencies", [])
        if isinstance(loaders, dict):
            return loaders.get("forge") or loaders.get("fabric")
    if manifests.packwiz:
        loader_info = manifests.packwiz.get("versions", {})
        for candidate in ("forge", "neoforge", "fabric", "quilt"):
            if candidate in loader_info:
                return candidate
    return detect_loader_from_mods(mods)


def compute_hash(path: Path) -> str:
    hasher = hashlib.sha1()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_fabric_metadata(zf: zipfile.ZipFile) -> Optional[Dict]:
    for name in ("fabric.mod.json", "quilt.mod.json"):
        if name in zf.namelist():
            return json.loads(zf.read(name))
    return None


def load_forge_metadata(zf: zipfile.ZipFile) -> Optional[Dict]:
    for name in ("META-INF/mods.toml", "META-INF/neoforge.mods.toml"):
        if name in zf.namelist():
            data = tomllib.loads(zf.read(name).decode("utf-8"))
            return data
    return None


def parse_dependencies_from_fabric(metadata: Dict) -> List[Dep]:
    deps: List[Dep] = []
    depends = metadata.get("depends", {})
    if isinstance(depends, dict):
        for key, value in depends.items():
            if key == "minecraft":
                continue
            if isinstance(value, list):
                version = ",".join(str(v) for v in value)
            else:
                version = str(value)
            deps.append(Dep(modid=key, version_range=version or None))
    return deps


def parse_dependencies_from_forge(metadata: Dict) -> List[Dep]:
    deps: List[Dep] = []
    if not metadata:
        return deps
    mods = metadata.get("mods", [])
    if not isinstance(mods, list):
        return deps
    for mod_entry in mods:
        rels = mod_entry.get("dependencies") or []
        for dep_entry in rels:
            modid = dep_entry.get("modId") or dep_entry.get("modid")
            if not modid:
                continue
            version_range = dep_entry.get("versionRange") or dep_entry.get("version_range")
            mandatory = dep_entry.get("mandatory", True)
            deps.append(Dep(modid=modid, version_range=version_range, required=bool(mandatory)))
    return deps


def parse_mod_metadata(jar_path: Path) -> Mod:
    mod_id = jar_path.stem
    mod_name = jar_path.stem
    version = None
    loader: Optional[str] = None
    dependencies: List[Dep] = []
    hashes = {"sha1": compute_hash(jar_path)}
    try:
        with zipfile.ZipFile(jar_path) as zf:
            fabric_meta = load_fabric_metadata(zf)
            if fabric_meta:
                loader = "fabric" if "fabric.mod.json" in zf.namelist() else "quilt"
                mod_id = fabric_meta.get("id", mod_id)
                mod_name = fabric_meta.get("name", mod_name)
                version = fabric_meta.get("version")
                dependencies.extend(parse_dependencies_from_fabric(fabric_meta))
            forge_meta = load_forge_metadata(zf)
            if forge_meta:
                loader = forge_meta.get("modLoader") or loader or "forge"
                if forge_meta.get("mods"):
                    primary = forge_meta["mods"][0]
                    mod_id = primary.get("modId", mod_id)
                    mod_name = primary.get("displayName", mod_name)
                    version = primary.get("version") or version
                dependencies.extend(parse_dependencies_from_forge(forge_meta))
            manifest_name = next((n for n in zf.namelist() if n.endswith("MANIFEST.MF")), None)
            if manifest_name and not fabric_meta and not forge_meta:
                manifest_text = zf.read(manifest_name).decode("utf-8", errors="ignore")
                for line in manifest_text.splitlines():
                    if line.lower().startswith("implementation-title"):
                        mod_name = line.split(":", 1)[-1].strip() or mod_name
                    if line.lower().startswith("implementation-version"):
                        version = line.split(":", 1)[-1].strip() or version
    except zipfile.BadZipFile:
        st.warning(f"{jar_path.name} no es un archivo JAR válido.")
    return Mod(
        id=mod_id,
        name=mod_name,
        filename=jar_path.name,
        path=jar_path,
        version=version,
        loader=loader,
        enabled=True,
        hashes=hashes,
        dependencies=dependencies,
        incompatibilities=[],
    )


def discover_mods(root: Path) -> List[Mod]:
    mods: List[Mod] = []
    mods_dir = root / "mods"
    disabled_dir = root / "mods_disabled"

    if mods_dir.exists():
        for jar_path in sorted(mods_dir.glob("*.jar")):
            mod = parse_mod_metadata(jar_path)
            mod.enabled = True
            mods.append(mod)
        # Compatibilidad con mods renombrados a .disabled
        for jar_path in sorted(mods_dir.glob("*.jar.disabled")):
            mod = parse_mod_metadata(jar_path)
            mod.enabled = False
            mods.append(mod)

    if disabled_dir.exists():
        for jar_path in sorted(disabled_dir.glob("*.jar")):
            mod = parse_mod_metadata(jar_path)
            mod.enabled = False
            mods.append(mod)

    return mods


def discover_configs(root: Path, immutable_root: Path) -> List[ConfigFile]:
    configs: List[ConfigFile] = []
    for directory in CONFIG_DIR_NAMES:
        working_dir = root / directory
        if not working_dir.exists():
            continue
        immutable_dir = immutable_root / directory
        for file in working_dir.rglob("*"):
            if file.is_file():
                rel_path = file.relative_to(root)
                fmt = file.suffix.lower().lstrip(".") or "txt"
                content = file.read_text(errors="ignore")
                immutable_file = immutable_dir / file.relative_to(working_dir)
                original_content = immutable_file.read_text(errors="ignore") if immutable_file.exists() else content
                configs.append(
                    ConfigFile(
                        path=file,
                        relative_path=rel_path,
                        format=fmt,
                        original_content=original_content,
                        content=content,
                    )
                )
    return configs


def discover_assets(root: Path, relative: str) -> List[Path]:
    directory = root / relative
    if not directory.exists():
        return []
    return sorted([p.relative_to(root) for p in directory.iterdir()])


def build_validation(mods: List[Mod], loader: Optional[str] = None) -> ValidationResult:
    result = ValidationResult()
    active_mods = [mod for mod in mods if mod.enabled]
    seen_hashes: Dict[str, List[str]] = {}
    mod_ids = {mod.id for mod in active_mods}
    for mod in active_mods:
        sha1 = mod.hashes.get("sha1")
        if not sha1:
            continue
        seen_hashes.setdefault(sha1, []).append(mod.name)
    duplicates = [names for names in seen_hashes.values() if len(names) > 1]
    for dup_group in duplicates:
        warning = f"Duplicado detectado: {', '.join(dup_group)}"
        result.warnings.append(warning)
        result.suggestions.append("Revisa los mods duplicados y deja solo una versión habilitada.")
    for mod in active_mods:
        for dep in mod.dependencies:
            if dep.required and dep.modid not in mod_ids:
                message = (
                    f"{mod.name} requiere {dep.modid} "
                    f"({dep.version_range or 'sin versión especificada'})"
                )
                result.errors.append(message)
                result.suggestions.append(
                    f"Añade {dep.modid} al pack o vuelve a habilitarlo para satisfacer las dependencias de {mod.name}."
                )
    if loader:
        normalized_loader = loader.lower()
        expected_family = LOADER_FAMILIES.get(normalized_loader, {normalized_loader})
        for mod in active_mods:
            if mod.loader and mod.loader.lower() not in expected_family:
                result.warnings.append(
                    f"{mod.name} parece ser un mod para {mod.loader}, que puede no ser compatible con {loader}."
                )
                result.suggestions.append(
                    f"Valida si {mod.name} requiere cambiar el loader o busca una versión compatible con {loader}."
                )
    if not active_mods:
        result.warnings.append("No se encontraron mods en la carpeta /mods.")
    if result.suggestions:
        result.suggestions = list(dict.fromkeys(result.suggestions))
    return result


def disable_mod(mod: Mod, pack: Pack) -> bool:
    if not mod.enabled:
        return False
    mods_disabled = pack.working_root / "mods_disabled"
    mods_disabled.mkdir(exist_ok=True)
    target = mods_disabled / mod.path.name
    try:
        shutil.move(str(mod.path), target)
    except OSError as exc:
        st.error(f"No se pudo deshabilitar {mod.name}: {exc}")
        return False
    mod.path = target
    mod.filename = target.name
    mod.enabled = False
    return True


def enable_mod(mod: Mod, pack: Pack) -> bool:
    if mod.enabled:
        return False
    mods_dir = pack.working_root / "mods"
    mods_dir.mkdir(exist_ok=True)
    current_path = mod.path
    if current_path.suffix == ".disabled":
        target = Path(str(current_path)[: -len(".disabled")])
    else:
        target = mods_dir / current_path.name
    if target.exists():
        st.error(
            f"Ya existe un archivo llamado {target.name} en mods/. Renombra o elimina el duplicado antes de habilitar {mod.name}."
        )
        return False
    try:
        shutil.move(str(current_path), target)
    except OSError as exc:
        st.error(f"No se pudo habilitar {mod.name}: {exc}")
        return False
    mod.path = target
    mod.filename = target.name
    mod.enabled = True
    return True


def hydrate_configs(pack: Pack):
    for cfg in pack.configs:
        current_content = cfg.path.read_text(errors="ignore")
        cfg.content = current_content


def load_pack(upload) -> Pack:
    workspace = get_temp_workspace()
    archive = save_upload(upload, workspace)
    root = extract_upload(archive, workspace)
    immutable_root = workspace / "immutable"
    working_root = workspace / "working"
    if immutable_root.exists():
        shutil.rmtree(immutable_root)
    if working_root.exists():
        shutil.rmtree(working_root)
    shutil.copytree(root, immutable_root)
    shutil.copytree(root, working_root)

    manifests = parse_manifest(working_root)
    mods = discover_mods(working_root)
    configs = discover_configs(working_root, immutable_root)
    datapacks = discover_assets(working_root, DATA_PACK_DIR)
    resourcepacks = discover_assets(working_root, RESOURCE_PACK_DIR)
    shaderpacks = discover_assets(working_root, SHADER_PACK_DIR)
    mc_version = detect_mc_version(manifests)
    loader = detect_loader(manifests, mods)
    validation = build_validation(mods, loader)
    name = manifests.curseforge.get("name") if manifests.curseforge else upload.name
    pack = Pack(
        name=name,
        mc_version=mc_version,
        loader=loader,
        working_root=working_root,
        immutable_root=immutable_root,
        manifests=manifests,
        mods=mods,
        configs=configs,
        datapacks=datapacks,
        resourcepacks=resourcepacks,
        shaderpacks=shaderpacks,
        validation=validation,
    )
    return pack


def render_overview_tab(pack: Pack):
    st.subheader("Estado general del pack")
    cols = st.columns(4)
    cols[0].metric("Minecraft", pack.mc_version or "Desconocido")
    cols[1].metric("Loader", pack.loader or "Desconocido")
    cols[2].metric("Mods", len(pack.mods))
    cols[3].metric("Configs", len(pack.configs))

    if pack.validation.errors:
        st.error("\n".join(pack.validation.errors))
    if pack.validation.warnings:
        st.warning("\n".join(pack.validation.warnings))

    if pack.manifests.curseforge:
        st.markdown("### Manifest de CurseForge")
        st.json(pack.manifests.curseforge)
    if pack.manifests.modrinth:
        st.markdown("### Manifest de Modrinth")
        st.json(pack.manifests.modrinth)
    if pack.manifests.packwiz:
        st.markdown("### Manifest de packwiz")
        st.json(pack.manifests.packwiz)


def render_dependency_graph(pack: Pack):
    edges = []
    active_mods = [mod for mod in pack.mods if mod.enabled]
    for mod in active_mods:
        for dep in mod.dependencies:
            edges.append((mod.name, dep.modid))
    if not edges:
        st.info("No hay dependencias declaradas en los metadatos analizados.")
        return
    dot_lines = ["digraph dependencies {", "rankdir=LR;"]
    for mod in active_mods:
        dot_lines.append(f'"{mod.name}" [shape=box]')
    for source, target in edges:
        dot_lines.append(f'"{source}" -> "{target}"')
    dot_lines.append("}")
    st.graphviz_chart("\n".join(dot_lines))


def render_mods_tab(pack: Pack):
    st.subheader("Gestor de mods")
    data = [
        {
            "ID": mod.id,
            "Nombre": mod.name,
            "Versión": mod.version or "?",
            "Loader": mod.loader or "?",
            "Archivo": mod.filename,
            "Carpeta": mod.path.parent.name,
            "SHA1": mod.hashes.get("sha1", ""),
            "Habilitado": mod.enabled,
            "Dependencias": ", ".join(dep.modid for dep in mod.dependencies) or "—",
        }
        for mod in pack.mods
    ]
    df = pd.DataFrame(data)
    edited = st.experimental_data_editor(df, num_rows="dynamic", use_container_width=True)
    st.caption(
        "Marca o desmarca la casilla de `Habilitado` para mover mods entre `mods/` y `mods_disabled/` en la copia de trabajo."
    )
    changes = []
    for idx, row in edited.iterrows():
        if idx >= len(pack.mods):
            continue
        mod = pack.mods[idx]
        desired_state = bool(row["Habilitado"])
        if desired_state == mod.enabled:
            continue
        toggled = enable_mod(mod, pack) if desired_state else disable_mod(mod, pack)
        if toggled:
            changes.append(mod.name)
    if changes:
        pack.validation = build_validation(pack.mods, pack.loader)
        st.success("Se actualizaron los estados: " + ", ".join(changes))

    st.markdown("### Duplicados y conflictos")
    duplicates = [w for w in pack.validation.warnings if "Duplicado" in w]
    if duplicates:
        for dup in duplicates:
            st.warning(dup)
    else:
        st.success("No se detectaron duplicados por hash.")

    st.markdown("### Grafo de dependencias")
    render_dependency_graph(pack)


def render_config_diff(config: ConfigFile, edited_content: str):
    import difflib

    diff = difflib.unified_diff(
        config.original_content.splitlines(),
        edited_content.splitlines(),
        fromfile="original",
        tofile="editado",
        lineterm="",
    )
    st.code("\n".join(diff) or "Sin cambios respecto al original")


def render_configs_tab(pack: Pack):
    st.subheader("Editor de configuraciones")
    if not pack.configs:
        st.info("No se encontraron archivos de configuración.")
        return

    config_map = {str(cfg.relative_path): cfg for cfg in pack.configs}
    selected_path = st.selectbox("Selecciona un archivo", sorted(config_map.keys()))
    if not selected_path:
        return
    cfg = config_map[selected_path]

    st.markdown(f"**Ruta:** `{cfg.relative_path}`")
    edited_content = st.text_area(
        "Contenido",
        value=st.session_state.setdefault("config_edits", {}).get(selected_path, cfg.content),
        height=400,
    )
    st.session_state.config_edits[selected_path] = edited_content

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Guardar cambios"):
            cfg.path.write_text(edited_content)
            cfg.content = edited_content
            st.success("Archivo guardado en la copia de trabajo.")
        if st.button("Revertir al original"):
            cfg.path.write_text(cfg.original_content)
            cfg.content = cfg.original_content
            st.session_state.config_edits[selected_path] = cfg.original_content
            st.info("Cambios revertidos.")
    with col2:
        st.markdown("**Diff vs original**")
        render_config_diff(cfg, edited_content)


def render_scripts_tab(pack: Pack):
    st.subheader("Workspace de scripts (KubeJS)")
    kube_root = pack.working_root / "kubejs"
    if not kube_root.exists():
        st.info("No se encontró carpeta kubejs en el pack.")
        return
    files = sorted([p.relative_to(pack.working_root) for p in kube_root.rglob("*.js")])
    if not files:
        st.info("No hay scripts JS para mostrar.")
        return
    selected = st.selectbox("Selecciona un script", [str(p) for p in files])
    script_path = pack.working_root / selected
    content = script_path.read_text(errors="ignore")
    st.text_area("Editor", value=content, height=400, key=f"script_{selected}")
    st.caption("Edición básica habilitada. Integración completa con Monaco/Ace es una futura mejora.")


def render_data_tab(pack: Pack):
    st.subheader("Data packs / Recursos / Shaders")
    col1, col2, col3 = st.columns(3)
    col1.markdown("### Datapacks")
    if pack.datapacks:
        col1.write("\n".join(f"• {p}" for p in pack.datapacks))
    else:
        col1.info("Sin datapacks detectados")

    col2.markdown("### Resourcepacks")
    if pack.resourcepacks:
        col2.write("\n".join(f"• {p}" for p in pack.resourcepacks))
    else:
        col2.info("Sin resourcepacks detectados")

    col3.markdown("### Shaderpacks")
    if pack.shaderpacks:
        col3.write("\n".join(f"• {p}" for p in pack.shaderpacks))
    else:
        col3.info("Sin shaderpacks detectados")


def render_diagnostics_tab(pack: Pack):
    st.subheader("Diagnósticos y validaciones")
    st.markdown("### Resultados de validación")
    if pack.validation.errors:
        st.error("\n".join(pack.validation.errors))
    else:
        st.success("Sin errores críticos detectados en dependencias.")
    if pack.validation.warnings:
        st.warning("\n".join(pack.validation.warnings))
    else:
        st.info("Sin advertencias adicionales.")
    if pack.validation.suggestions:
        st.markdown("### Sugerencias automáticas")
        for suggestion in pack.validation.suggestions:
            st.info(suggestion)
    else:
        st.caption("No hay sugerencias adicionales en este análisis.")

    logs_dir = pack.working_root / "logs"
    latest_log = logs_dir / "latest.log"
    if latest_log.exists():
        st.markdown("### latest.log (fragmento)")
        st.text(latest_log.read_text(errors="ignore")[-5000:])
    else:
        st.caption("Sube tus logs en la carpeta /logs para obtener análisis adicionales en futuras versiones.")


def create_zip_bytes(root: Path) -> io.BytesIO:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in root.rglob("*"):
            if file.is_file():
                zf.write(file, arcname=file.relative_to(root))
    buffer.seek(0)
    return buffer


def render_export_tab(pack: Pack):
    st.subheader("Exportar pack")
    st.markdown("Prepara una exportación rápida del workspace actual.")

    export_zip = create_zip_bytes(pack.working_root)
    st.download_button(
        label="Descargar ZIP (modo laboratorio)",
        data=export_zip,
        file_name=f"{pack.name or 'pack'}-export.zip",
        mime="application/zip",
    )

    st.markdown("### Changelog básico")
    mod_lines = [
        f"{'✓' if mod.enabled else '✗'} {mod.name} ({mod.version or 'desconocida'})"
        for mod in pack.mods
    ]
    st.text("Mods detectados:\n" + "\n".join(mod_lines))
    if st.session_state.get("config_edits"):
        changed = [path for path, content in st.session_state.config_edits.items() if content]
        st.text("Configuraciones editadas:\n" + "\n".join(changed))
    else:
        st.caption("Sin cambios registrados en configuraciones en esta sesión.")


def sidebar(pack: Optional[Pack]):
    with st.sidebar:
        st.markdown("## Pack manager")
        st.markdown("Crea un workspace temporal para inspeccionar y modificar tus packs de Minecraft.")
        upload = st.file_uploader("Importar pack", type=[ext.lstrip(".") for ext in SUPPORTED_UPLOADS])
        if upload is not None:
            try:
                st.session_state.pack = load_pack(upload)
                st.success("Pack importado correctamente. Usa las pestañas para explorarlo.")
            except zipfile.BadZipFile:
                st.error("El archivo seleccionado no es un paquete comprimido válido.")
            except Exception as exc:  # pragma: no cover - errores inesperados
                st.exception(exc)
        st.markdown("---")
        if pack:
            st.markdown(f"**Nombre:** {pack.name}")
            st.markdown(f"**Minecraft:** {pack.mc_version or '—'}")
            st.markdown(f"**Loader:** {pack.loader or '—'}")
            st.markdown(f"**Mods:** {len(pack.mods)}")
            st.markdown(f"**Configs:** {len(pack.configs)}")
            st.caption(f"Workspace: {pack.working_root}")
        st.markdown("---")
        st.markdown("### Acciones rápidas")
        if pack and st.button("Refrescar datos"):
            hydrate_configs(pack)
            pack.validation = build_validation(pack.mods, pack.loader)
            st.experimental_rerun()


def main():
    st.set_page_config(page_title="PackSmith", layout="wide", page_icon="🧰")
    st.title("🧰 PackSmith - Laboratorio de modpacks")
    st.caption(
        "Importa, analiza y ajusta tus modpacks de Minecraft con una experiencia de escritorio optimizada."
    )

    pack: Optional[Pack] = st.session_state.get("pack")
    sidebar(pack)

    if not pack:
        st.info("Importa un modpack para comenzar. Aceptamos exportaciones de CurseForge y Modrinth en formato ZIP/MRPACK.")
        return

    tabs = st.tabs([
        "Overview",
        "Mods",
        "Configs",
        "Scripts",
        "Data / Resources",
        "Diagnostics",
        "Export",
    ])

    with tabs[0]:
        render_overview_tab(pack)
    with tabs[1]:
        render_mods_tab(pack)
    with tabs[2]:
        render_configs_tab(pack)
    with tabs[3]:
        render_scripts_tab(pack)
    with tabs[4]:
        render_data_tab(pack)
    with tabs[5]:
        render_diagnostics_tab(pack)
    with tabs[6]:
        render_export_tab(pack)


if __name__ == "__main__":
    main()
