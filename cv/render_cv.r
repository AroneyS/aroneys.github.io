# Builds the CV (HTML + PDF) and the short resume (PDF).
# Run from cv/ via `pixi run -e cv cv`; outputs go to ../assets/cv/ (not tracked by git).
# Before rendering, regenerate data/articles.tsv from the bibliography:
#   pixi run python scripts/bib_to_cv.py
out_dir <- "../assets/cv"
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

render_pdf <- function(resume_mode, pdf_name) {
  tmp_html <- fs::file_temp(ext = ".html")
  rmarkdown::render("cv.rmd",
                    params = list(pdf_mode = TRUE, resume_mode = resume_mode),
                    output_file = tmp_html, quiet = TRUE)
  pagedown::chrome_print(input = tmp_html, output = file.path(out_dir, pdf_name),
                         extra_args = c("--no-sandbox"))
}

# Full HTML (web version with links)
rmarkdown::render("cv.rmd",
                  params = list(pdf_mode = FALSE, resume_mode = FALSE),
                  output_file = "cv.html", output_dir = out_dir, quiet = TRUE)

render_pdf(FALSE, "cv.pdf")
render_pdf(TRUE, "resume.pdf")
