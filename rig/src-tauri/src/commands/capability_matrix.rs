use std::path::Path;

#[derive(serde::Serialize, Clone)]
pub struct MatrixAgent {
    pub file:  String,
    pub label: String,
    pub tools: Vec<String>,
}

#[derive(serde::Serialize, Clone)]
pub struct MatrixScript {
    pub file:    String,
    pub purpose: String,
}

#[derive(serde::Serialize, Clone)]
pub struct MatrixUseCase {
    pub title:   String,
    pub agents:  Vec<MatrixAgent>,
    pub scripts: Vec<MatrixScript>,
}

#[derive(serde::Serialize)]
pub struct CapabilityMatrix {
    pub use_cases:    Vec<MatrixUseCase>,
    pub generated_at: Option<String>,
}

#[tauri::command]
pub fn capability_matrix_load() -> Result<CapabilityMatrix, String> {
    let agents_path = std::env::var("AETHERIS_AGENTS_PATH")
        .map_err(|_| "AETHERIS_AGENTS_PATH not set".to_string())?;

    let path = Path::new(&agents_path)
        .join("docs")
        .join("capability-matrix.md");

    let raw = std::fs::read_to_string(&path)
        .map_err(|e| format!("read failed: {}", e))?;

    parse_matrix(&raw)
}

fn parse_matrix(raw: &str) -> Result<CapabilityMatrix, String> {
    let mut use_cases: Vec<MatrixUseCase> = vec![];
    let mut current_uc: Option<MatrixUseCase> = None;
    let mut in_agents_table  = false;
    let mut in_scripts_table = false;
    let mut generated_at: Option<String> = None;

    for line in raw.lines() {
        let line = line.trim();

        if line.starts_with("_Generated") {
            generated_at = Some(line.trim_matches('_').to_string());
            continue;
        }

        if line.starts_with("## ") {
            if let Some(uc) = current_uc.take() {
                use_cases.push(uc);
            }
            current_uc = Some(MatrixUseCase {
                title:   line.trim_start_matches("## ").to_string(),
                agents:  vec![],
                scripts: vec![],
            });
            in_agents_table  = false;
            in_scripts_table = false;
            continue;
        }

        if line.starts_with("### Agents") {
            in_agents_table  = true;
            in_scripts_table = false;
            continue;
        }
        if line.starts_with("### Scripts") {
            in_scripts_table = true;
            in_agents_table  = false;
            continue;
        }

        if !line.starts_with('|') { continue; }
        if line.contains("---") { continue; }
        if line.contains("Agent file") || line.contains("Script") { continue; }

        let cols: Vec<&str> = line
            .split('|')
            .map(|c| c.trim())
            .filter(|c| !c.is_empty())
            .collect();

        if let Some(ref mut uc) = current_uc {
            if in_agents_table && cols.len() >= 3 {
                let tools: Vec<String> = cols[2]
                    .split(',')
                    .map(|t| t.trim().trim_matches('`').to_string())
                    .filter(|t| !t.is_empty())
                    .collect();
                uc.agents.push(MatrixAgent {
                    file:  cols[0].to_string(),
                    label: cols[1].to_string(),
                    tools,
                });
            } else if in_scripts_table && cols.len() >= 2 {
                uc.scripts.push(MatrixScript {
                    file:    cols[0].to_string(),
                    purpose: cols[1].to_string(),
                });
            }
        }
    }

    if let Some(uc) = current_uc {
        use_cases.push(uc);
    }

    let use_cases = use_cases
        .into_iter()
        .filter(|uc| !uc.agents.is_empty() || !uc.scripts.is_empty())
        .collect();

    Ok(CapabilityMatrix { use_cases, generated_at })
}
