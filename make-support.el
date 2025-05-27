;;; make-support.el --- Support functions for Makefile tasks

;;; Commentary:
;; This file contains Emacs Lisp functions used by the Makefile
;; for org-mode operations like tangling, linting, and publishing.

;;; Code:

(require 'org)
(require 'org-lint)

(defun org-tangle-to-subdirectory (org-file)
  "Tangle ORG-FILE to a subdirectory named after the file."
  (let* ((file-name (file-name-nondirectory org-file))
         (base-name (file-name-sans-extension file-name))
         (org-dir (file-name-directory org-file))
         (target-dir (expand-file-name base-name org-dir)))
    
    ;; Create target directory without prompting
    (make-directory target-dir t)
    
    ;; Tangle with modified default directory and suppress prompts
    (let ((default-directory target-dir)
          (org-babel-tangle-use-relative-file-links t)
          (org-src-preserve-indentation t)
          (org-confirm-babel-evaluate nil)
          (org-babel-confirm-evaluate-answer-no t))
      (org-babel-tangle-file (expand-file-name org-file)))))

(defun batch-org-tangle ()
  "Tangle org files from command line arguments."
  (let ((files command-line-args-left)
        (org-confirm-babel-evaluate nil)
        (org-babel-confirm-evaluate-answer-no t))
    (dolist (file files)
      (when (file-exists-p file)
        (message "Tangling %s..." file)
        (condition-case err
            (with-current-buffer (find-file-noselect file)
              (let ((tangled-files (org-babel-tangle)))
                (if tangled-files
                    (message "Tangled %d code blocks from %s" (length tangled-files) file)
                  (message "Tangled 0 code blocks from %s" file))))
          (error (message "Error tangling %s: %s" file (error-message-string err))))))))

(defun batch-org-lint ()
  "Lint org files from command line arguments."
  (let ((files command-line-args-left)
        (total-issues 0))
    (dolist (file files)
      (when (file-exists-p file)
        (message "Linting %s..." file)
        (condition-case err
            (with-current-buffer (find-file-noselect file)
              (let ((issues (org-lint)))
                (when issues
                  (setq total-issues (+ total-issues (length issues)))
                  (dolist (issue issues)
                    (message "  %s:%d: %s"
                             file
                             (org-lint-issue-line issue)
                             (org-lint-issue-description issue))))))
          (error (message "  Error: %s" (error-message-string err))))))
    (when (> total-issues 0)
      (kill-emacs 1))))  ; Exit with error if issues found

(defun batch-org-to-markdown ()
  "Convert org files to markdown."
  (require 'ox-md)
  (let ((files command-line-args-left))
    (dolist (file files)
      (when (file-exists-p file)
        (message "Converting %s to markdown..." file)
        (condition-case err
            (with-current-buffer (find-file-noselect file)
              (let ((output-file (concat (file-name-sans-extension file) ".md")))
                (org-export-to-file 'md output-file)
                (message "  Created %s" output-file)))
          (error (message "  Error: %s" (error-message-string err))))))))

;; Enable Babel languages
(org-babel-do-load-languages
 'org-babel-load-languages
 '((python . t)
   (shell . t)))

;; Optional: Set Python interpreter (if you want to specify)
(setq org-babel-python-command "python3")

;; Optional: Don't ask for confirmation when executing code blocks
(setq org-confirm-babel-evaluate nil)

;; Optional: Set default header arguments for specific languages
(setq org-babel-default-header-args:python
      '((:results . "output")
        (:session . "python-default")))

(setq org-babel-default-header-args:shell
      '((:results . "output")
        (:shebang . "#!/bin/bash")))

;; Optional: Enable :mkdirp globally for all blocks
(setq org-babel-default-header-args
      (cons '(:mkdirp . "yes")
            org-babel-default-header-args))

;; Optional: Set up tangling defaults
(setq org-src-preserve-indentation t)  ; Preserve indentation when tangling
(setq org-edit-src-content-indentation 0)  ; Don't indent src block content

(provide 'make-support)
;;; make-support.el ends here
