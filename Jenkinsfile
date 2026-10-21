
pipeline {
    agent any

    options {
        timestamps()
    }

    environment {
        IMAGE_NAME = 'ai-medical-risk-management'
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Source code checked out by Jenkins from GitHub.'
            }
        }

        stage('Validate Project') {
            steps {
                sh '''
                    test -f app.py
                    test -f requirements.txt
                    python -m py_compile app.py
                    echo "Project files and Python syntax validated."
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t ${IMAGE_NAME}:${BUILD_NUMBER} .'
            }
        }

        stage('Deploy Application') {
            steps {
                sh '''
                    docker stop ai-medical-risk-management-cicd || true
                    docker rm ai-medical-risk-management-cicd || true

                    docker run -d \
                      --name ai-medical-risk-management-cicd \
                      --restart unless-stopped \
                      -p 8502:8501 \
                      ${IMAGE_NAME}:${BUILD_NUMBER}
                '''
            }
        }
    }

    post {
        success {
            echo 'CI/CD pipeline completed successfully.'
            echo 'Application URL: http://localhost:8502'
        }
        failure {
            echo 'Pipeline failed. Check the Jenkins Console Output.'
        }
    }
}
