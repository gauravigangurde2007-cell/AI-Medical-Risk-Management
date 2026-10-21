
pipeline {
    agent any

    options {
        timestamps()
    }

    environment {
        IMAGE_NAME = 'ai-medical-risk-management'
        CONTAINER_NAME = 'ai-medical-risk-management-app'
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Source code checked out from GitHub.'
            }
        }

        stage('Validate Project') {
            steps {
                sh '''
                    set -e
                    test -f app.py
                    test -f requirements.txt
                    docker run --rm \
                        -v "$WORKSPACE:/app" \
                        -w /app \
                        python:3.12-slim \
                        python -m py_compile app.py
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                    set -e
                    docker build -t ${IMAGE_NAME}:latest .
                '''
            }
        }

        stage('Deploy Application') {
            steps {
                sh '''
                    set -e
                    docker rm -f ${CONTAINER_NAME} || true
                    docker run -d \
                        --name ${CONTAINER_NAME} \
                        --restart unless-stopped \
                        -p 8501:8501 \
                        ${IMAGE_NAME}:latest
                '''
            }
        }

        stage('Verify Deployment') {
            steps {
                sh '''
                    sleep 10
                    docker ps --filter "name=${CONTAINER_NAME}"
                    docker logs --tail 30 ${CONTAINER_NAME}
                '''
            }
        }
    }

    post {
        success {
            echo 'CI/CD pipeline completed successfully.'
            echo 'Open the application at http://localhost:8501'
        }
        failure {
            echo 'Pipeline failed. Check Console Output for the failing stage.'
        }
    }
}
