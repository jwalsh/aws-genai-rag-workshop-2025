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
    
    ;; Create target directory
    (make-directory target-dir t)
    
    ;; Tangle with modified default directory
    (let ((default-directory target-dir)
          (org-babel-tangle-use-relative-file-links t)
          (org-src-preserve-indentation t))
      (org-babel-tangle-file (expand-file-name org-file)))))

(defun batch-org-tangle ()
  "Tangle org files from command line arguments."
  (let ((files command-line-args-left))
    (dolist (file files)
      (when (file-exists-p file)
        (message "Tangling %s..." file)
        (condition-case err
            (let ((tangled-files (org-tangle-to-subdirectory file)))
              (if tangled-files
                  (message "  Tangled %d files" (length tangled-files))
                (message "  No files to tangle")))
          (error (message "  Error: %s" (error-message-string err))))))))

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

(provide 'make-support)
;;; make-support.el ends here