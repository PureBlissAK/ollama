# ==============================================================================
# Agentic Infrastructure Outputs
# ==============================================================================

output "agents_service_url" {
  description = "Cloud Run agents service public URL"
  value       = google_cloud_run_service.agents.status[0].url
}

output "agents_service_name" {
  description = "Cloud Run agents service name"
  value       = google_cloud_run_service.agents.name
}

output "orchestrator_service_url" {
  description = "Cloud Run orchestrator service public URL"
  value       = google_cloud_run_service.orchestrator.status[0].url
}

output "orchestrator_service_name" {
  description = "Cloud Run orchestrator service name"
  value       = google_cloud_run_service.orchestrator.name
}

output "task_queue_name" {
  description = "Cloud Tasks queue name for agent job distribution"
  value       = google_cloud_tasks_queue.agent_tasks.name
}

output "agent_results_topic" {
  description = "Pub/Sub topic for agent execution results"
  value       = google_pubsub_topic.agent_results.name
}

output "artifacts_repository" {
  description = "Artifact Registry repository for agent images"
  value       = google_artifact_registry_repository.agents.repository_id
}

output "firestore_database" {
  description = "Firestore database for agent state"
  value       = google_firestore_database.agents.name
}

output "logs_dataset" {
  description = "BigQuery dataset for agent execution logs and analytics"
  value       = google_bigquery_dataset.agent_logs.dataset_id
}

output "service_account_agents" {
  description = "Service account email for agent service"
  value       = google_service_account.agents.email
}

output "service_account_orchestrator" {
  description = "Service account email for orchestrator service"
  value       = google_service_account.orchestrator.email
}

output "deployment_info" {
  description = "Summary of agentic infrastructure deployment"
  value = {
    component       = "prod-ollama-agents"
    region          = var.region
    agents_service  = google_cloud_run_service.agents.name
    orchestrator    = google_cloud_run_service.orchestrator.name
    environment     = var.environment
    compliance      = "Landing Zone 8-Point Mandate ✅"
  }
}
