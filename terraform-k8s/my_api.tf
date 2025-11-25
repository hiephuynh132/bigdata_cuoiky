resource "kubernetes_deployment" "my_api" {
  metadata {
    name      = "my-api"
    namespace = "${var.namespace}"
    labels = {
      "k8s.service" = "my-api"
    }
  }

  depends_on = [
    kubernetes_deployment.kafkaservice
  ]

  spec {
    replicas = 1

    selector {
      match_labels = {
        "k8s.service" = "my-api"
      }
    }

    template {
      metadata {
        labels = {
          "k8s.network/pipeline-network" = "true"
          "k8s.service" = "my-api"
        }
      }

      spec {
        restart_policy = "Always"

        container {
          name  = "my-api"
          image = "local/my-api:latest" # đổi theo image của bạn
          image_pull_policy = "IfNotPresent"
          port {
            container_port = 36000 # đổi nếu API của bạn chạy port khác trong container
          }

          env {
            name  = "KAFKA_BOOTSTRAP_SERVERS"
            value = "kafkaservice:29092"
          }

          env {
            name  = "TOPIC_NAME"
            value = "redditcomments"
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "my_api" {
  metadata {
    name      = "my-api"
    namespace = var.namespace
    labels = {
      app = "my-api"
    }
  }

  depends_on = [
    kubernetes_deployment.my_api
  ]

  spec {
    type = "ClusterIP"

    port {
      name        = "http"
      port        = 36000
      target_port = 36000
      protocol    = "TCP"
    }

    selector = {
      "k8s.service" = "my-api"
    }
  }
}

