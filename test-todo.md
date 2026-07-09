# Test Implementation Roadmap — blockchain_privacy_platform

**Estimated total:** ~350–400 tests across 11 Django apps

---

## Phase 0: Test Infrastructure

### Files to create
| File | Purpose |
|---|---|
| `conftest.py` (project root) | pytest configuration, Django settings module |
| `privacy_platform/test_utils.py` | Shared factory functions for all test objects |
| `privacy_tools/tests/__init__.py` | Package init |
| `experiments/tests/__init__.py` | Package init |
| `accounts/tests/__init__.py` | Package init |
| ... per-app `tests/__init__.py` | Package init for each app |

### Factory fixtures needed (`test_utils.py`)
- `create_user(user_type="researcher")` — User with configurable type
- `create_admin()` — staff/superuser
- `create_technique(technique_type="ring_signature")` — PrivacyTechnique with realistic defaults
- `create_dataset_csv(uploaded_by, rows=100)` — Dataset backed by `SimpleUploadedFile` CSV
- `create_experiment(user, technique, dataset, status="pending")` — Experiment in any status
- `create_completed_experiment(...)` — full experiment with fake metrics

---

## [x] Phase 1: Unit Tests — Privacy Techniques (`privacy_tools/tests/`)

| File | Class | Tests |
|---|---|---|
| `test_ring_signature.py` | `TestRingSignature` | `test_generate_key_pair`, `test_generate_ring_size`, `test_sign_verify_valid`, `test_sign_fails_without_key_in_ring`, `test_verify_rejects_tampered_message`, `test_verify_rejects_tampered_signature`, `test_evaluate_privacy_scales_with_ring_size`, `test_evaluate_privacy_unlinkability_formula` |
| `test_zero_knowledge_proof.py` | `TestZeroKnowledgeProof` | `test_generate_commitment`, `test_generate_proof`, `test_verify_proof_valid`, `test_verify_proof_invalid_tampered`, `test_prove_range_valid`, `test_prove_range_out_of_bounds_raises`, `test_evaluate_privacy` |
| `test_secure_mpc.py` | `TestSecureMultiPartyComputation` | `test_generate_shares_count`, `test_reconstruct_secret_with_threshold`, `test_reconstruct_fails_below_threshold`, `test_secure_sum_correct`, `test_secure_average_correct`, `test_joint_signature`, `test_verify_joint_signature`, `test_evaluate_privacy` |
| `test_trusted_execution.py` | `TestTrustedExecutionEnvironment` | `test_create_enclave`, `test_seal_unseal_roundtrip`, `test_unseal_fails_wrong_enclave`, `test_secure_compute_sum`, `test_secure_compute_average`, `test_secure_compute_hash`, `test_remote_attestation_verify`, `test_verify_attestation_rejects_wrong_challenge`, `test_evaluate_privacy` |
| `test_crypto_mixer.py` | `TestCryptocurrencyMixer` | `test_generate_address_format`, `test_create_deposit`, `test_mix_transactions_success`, `test_mix_fails_below_min_pool`, `test_withdraw_success`, `test_withdraw_invalid_code`, `test_withdraw_unmixed_deposit`, `test_analyze_anonymity`, `test_evaluate_privacy` |
| `test_models.py` | `TestPrivacyTechniqueModel` | `test_create`, `test_str`, `test_type_choices`, `test_security_level_validators`, `test_unique_name`, `test_audit_log_create`, `test_audit_log_update` |
| `test_forms.py` | `TestPrivacyTechniqueForm` | `test_valid`, `test_required_fields` |

---

## [x] Phase 2: Unit Tests — Experiment Runner (`experiments/tests/test_runner.py`)

| Class | Tests |
|---|---|
| `TestPrivacyExperimentRunner` | `test_unknown_technique_raises`, `test_ensure_accuracy_zero_total`, `test_ensure_accuracy_clamps_range`, `test_get_fallback_accuracy_all_techniques`, `test_calculate_privacy_score_basic`, `test_calculate_privacy_score_with_all_factors`, `test_calculate_privacy_score_security_level_mapping`, `test_calculate_privacy_score_respects_cap` |
| `TestRunnerRingSignature` | `test_run_returns_all_keys`, `test_run_with_empty_df`, `test_fallback_implementation` |
| `TestRunnerZKP` | `test_run_returns_all_keys`, `test_run_real_proof_verification` |
| `TestRunnerSMPC` | `test_run_returns_all_keys`, `test_run_shamir_reconstruction` |
| `TestRunnerTEE` | `test_run_returns_all_keys`, `test_run_aes_roundtrip` |
| `TestRunnerMixer` | `test_run_returns_all_keys`, `test_run_mixing_logic` |

---

## [x] Phase 3: Model Tests (per app `tests/test_models.py`)

| App | Class | Tests |
|---|---|---|
| **accounts** | `TestUserModel` | `test_create`, `test_create_superuser`, `test_str`, `test_user_type_choices`, `test_is_approved_default_true`, `test_ordering` |
| **datasets** | `TestDatasetModel` | `test_create`, `test_str`, `test_unique_constraint`, `test_is_approved/pending/rejected`, `test_file_extension`, `test_get_data_returns_dataframe`, `test_get_sample_data`, `test_save_calculates_file_size`, `test_delete_removes_file`, `test_audit_log_create`, `test_audit_log_status_change_approve` |
| **experiments** | `TestExperimentModel` | `test_create`, `test_str`, `test_unique_user_name`, `test_status_default`, `test_audit_log_create`, `test_audit_log_status_change` |
|  | `TestExperimentComparisonModel` | `test_create`, `test_str`, `test_many_to_many` |
| **audit** | `TestAuditLogModel` | `test_create`, `test_str`, `test_indexes`, `test_all_action_types` |
|  | `TestAuditableMixin` | `test_tracks_original_state`, `test_detects_changes`, `test_get_special_action_run/approve`, `test_save_logs_create/update`, `test_delete_logs_delete` |
| **admin_panel** | `TestExperimentErrorReport` | `test_create`, `test_resolve_workflow` |
|  | `TestSystemMetric` | `test_create`, `test_metric_name_choices` |
|  | `TestAdminNotification` | `test_create`, `test_mark_read` |
| **reports** | `TestReportTemplate` | `test_create`, `test_is_public_default` |
|  | `TestReport` | `test_create`, `test_report_types`, `test_file_field` |
|  | `TestReportSchedule` | `test_create`, `test_compute_next_run_daily/weekly/monthly` |
|  | `TestReportShare` | `test_create`, `test_unique_token`, `test_is_expired`, `test_is_active`, `test_record_access`, `test_revoked_inactive` |
| **notifications** | `TestNotificationModel` | `test_create`, `test_is_read_default_false` |
| **share** | `TestExperimentShare` | `test_create`, `test_unique_token`, `test_is_expired`, `test_is_active`, `test_record_access`, `test_revoked` |

---

## [x] Phase 4: Form Tests (per app `tests/test_forms.py`)

| App | Class | Tests |
|---|---|---|
| **accounts** | `TestUserRegistrationForm` | `test_valid`, `test_password_mismatch`, `test_password_too_short`, `test_duplicate_email`, `test_duplicate_username` |
|  | `TestUserProfileForm` | `test_valid`, `test_optional_fields` |
| **experiments** | `TestExperimentForm` | `test_valid`, `test_filters_dataset_by_user`, `test_filters_technique_by_active`, `test_validates_json_config`, `test_invalid_json`, `test_empty_config_returns_dict` |
|  | `TestExperimentComparisonForm` | `test_valid`, `test_filters_by_user_and_completed`, `test_requires_two_experiments`, `test_rejects_single` |
| **datasets** | `TestDatasetUploadForm` | `test_valid`, `test_rejects_invalid_extension` |
| **reports** | `TestReportGenerationForm` | `test_valid`, `test_optional` |
|  | `TestReportScheduleForm` | `test_valid_daily/weekly/monthly` |
|  | `TestReportTemplateForm` | `test_valid` |

---

## Phase 5: View Tests (per app `tests/test_views.py`)

### accounts
| View | Coverage |
|---|---|
| `register_view` | GET 200, POST creates user, POST redirects, POST rejects duplicate/mismatch |
| `login_view` | GET 200, POST valid credentials, POST invalid, redirect authenticated |
| `logout_view` | Requires login, logs out, redirects |
| `profile_view` | GET 200, POST updates, login_required |

### dashboard
| View | Coverage |
|---|---|
| `home_view` | GET 200, login_required, context has experiments |
| `techniques_overview` | GET 200, context includes techniques |

### datasets
| View | Coverage |
|---|---|
| `dataset_list` | GET 200, pagination, status filter |
| `dataset_upload` | GET 200, POST creates, POST validates file type |
| `dataset_detail` | GET 200, 404 for wrong user |
| `dataset_delete` | POST deletes, GET confirmation |

### experiments
| View | Coverage |
|---|---|
| `experiment_list` | GET 200, status filter, pagination |
| `results_dashboard` | GET 200, date/technique/dataset filters, chart context |
| `experiment_create` | GET 200, POST creates, form validation |
| `experiment_detail` | GET 200, charts for completed, 404 for wrong user |
| `experiment_export` | GET JSON/CSV, login_required |
| `run_experiment` | POST runs experiment, updates status, notifications, error reports on failure |
| `experiment_compare` | GET 200, POST creates comparison |
| `comparison_detail` | GET 200, ranking data, best/worst markers |
| `export_comparison` | GET CSV/PDF/HTML |
| `experiment_delete` | POST deletes, GET confirmation |

### admin_panel
| View | Coverage |
|---|---|
| `admin_dashboard` | GET 200, admin_required |
| `manage_users` | GET lists, POST toggles approval |
| `manage_datasets` | GET lists, POST approve/reject |
| `manage_techniques` | GET lists, POST add/edit/toggle |
| `admin_audit_logs` | GET lists, POST filters |
| `admin_notifications` | GET lists, mark-read, mark-all-read, unread-count JSON |
| `system_metric_trends` | GET returns JSON |
| `error_reports` | GET list, POST resolve |

### audit
| View | Coverage |
|---|---|
| `audit_log_list` | GET 200, pagination, admin_required |
| `audit_log_detail` | GET 200 |
| `audit_object_history` | GET filters by type + object_id |

### notifications
| View | Coverage |
|---|---|
| `notification_list` | GET 200, login_required |
| `mark_read` | GET marks single, returns JSON |
| `mark_all_read` | GET marks all, returns JSON |
| `unread_count` | GET returns JSON count |

### export
| View | Coverage |
|---|---|
| `export_experiments` | GET CSV/JSON/XLSX/ZIP, status/technique/date filters |
| `export_reports` | GET CSV/JSON/ZIP |

### share
| View | Coverage |
|---|---|
| `create_share_link` | GET/POST creates share, login_required |
| `shared_experiment_view` | GET public by token, 404 revoked/expired |
| `manage_links` | GET lists shares |
| `revoke_link` | GET revokes |

### reports (~20 endpoints)
| View family | Coverage |
|---|---|
| `report_list/generate/detail/download/delete` | Full CRUD, login_required |
| `schedule_*` | CRUD + toggle + compute_next_run |
| `template_*` | CRUD |
| `share_report/manage_shares/revoke_share` | Share workflow |
| `shared_report_view` | Public access by token |

---

## Phase 6: Management Command Tests

| Command | Key scenarios |
|---|---|
| `load_techniques` | Creates 5 rows, idempotent on rerun |
| `rerun_experiments` | `--ids`, `--limit`, `--force`, skips running, handles failure |
| `rerun_all_report` | `--force`, `--out csv`, generates report, error handling |
| `backfill_metrics` | Updates null metrics, respects completed status |
| `fix_all_accuracy` | Fixes null/zero accuracy values |
| `audit_consistency_check` | Detects orphaned records |
| `fix_orphaned_files` | Cleans up orphaned media files |
| `generate_missing_reports` | Creates reports for experiment without one |
| `report_data_fix` | Fixes null accuracy, recalculates summaries |
| `sync_audit_metrics` | Recalculates from raw experiment data |
| `seed_report_templates` | Creates 3 templates, idempotent |
| `process_scheduled_reports` | Checks next_run, generates report, updates next_run |
| `record_system_metrics` | Records all 4 metric types |
| `purge_audit_logs` | `--days`, `--dry-run`, date boundaries |
| `export_audit_logs` | Exports JSON, date filter |

---

## [x] Phase 7: Integration Tests

| # | Scenario |
|---|---|
| 1 | Full experiment: upload dataset → approve → create experiment → run → verify results + notification + audit log |
| 2 | Comparison: create & run 2 experiments → create comparison → verify ranking → export |
| 3 | Audit middleware: POST mutating endpoint → AuditLog created with correct changes |
| 4 | Report: complete experiment → generate report → download → share → access shared link |
| 5 | Registration to results: register → login → upload → create → run → view |
| 6 | Error: simulate failed run → verify ExperimentErrorReport → resolve in admin |
| 7 | Scheduled reports: create schedule → run `process_scheduled_reports` → verify report + next_run |
| 8 | Notifications: run experiment → verify Notification object + unread_count increase |

---

## Phase 8: Edge Cases

| # | Scenario |
|---|---|
| 1 | Empty dataset (0 rows, 0 columns) |
| 2 | Dataset with non-numeric / string-only columns |
| 3 | Ring signature with ring_size=1 |
| 4 | SMPC with threshold=1 |
| 5 | TEE with data_size=0 |
| 6 | Mixer with pool_size=0 |
| 7 | Experiment with empty/null configuration |
| 8 | Null/None metric values in comparison views |
| 9 | Expired share tokens |
| 10 | Revoked shares accessed after revocation |
| 11 | User with zero experiments views empty dashboard |
| 12 | Regular user blocked from admin_panel views |

---

## Test Conventions

- `setUpTestData` for class-level fixtures (speed)
- `unittest.mock.patch` for slow crypto ops in view/command tests
- `SimpleUploadedFile` for dataset file simulation
- One assertion per test where practical
- Common fixtures in `privacy_platform/test_utils.py`
- Management commands tested via `call_command`
- View tests via Django `Client` with `self.client.login()`
- Slow tests marked with `@pytest.mark.slow` (if pytest added later)

---

## Deliverables

All test files mirror the existing app structure under each app's `tests/` directory, using Django's built-in `TestCase` (no pytest dependency required). The existing boilerplate `tests.py` files get replaced with the full `tests/` package.
