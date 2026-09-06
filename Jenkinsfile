pipeline {
    agent any

    environment {
        AWS_REGION          = 'ap-south-1'
        AWS_ACCOUNT_ID      = credentials('aws-account-id')
        ECR_REGISTRY        = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
        BACKEND_IMAGE       = "${ECR_REGISTRY}/smart-travel-planner-backend"
        FRONTEND_IMAGE      = "${ECR_REGISTRY}/smart-travel-planner-frontend"
        IMAGE_TAG           = "${env.BUILD_NUMBER}"
        EKS_CLUSTER_NAME    = 'smart-travel-planner'
        K8S_NAMESPACE       = 'smart-travel-planner'
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Backend Tests') {
            steps {
                sh '''
                    python3 -m venv ci-venv
                    . ci-venv/bin/activate
                    pip install -r backend/requirements.txt
                    pytest backend/tests -v
                '''
            }
        }

        stage('Frontend Build') {
            steps {
                sh '''
                    cd frontend
                    npm ci
                    npm run build
                '''
            }
        }

        stage('Docker Build') {
            steps {
                sh '/usr/local/bin/docker-compose build'
            }
        }

        stage('Login to Amazon ECR') {
            when {
                branch 'main'
            }
            steps {
                withCredentials([[
                    $class: 'AmazonWebServicesCredentialsBinding',
                    credentialsId: 'aws-jenkins-deploy'
                ]]) {
                    sh '''
                        aws ecr get-login-password --region "$AWS_REGION" \
                            | docker login --username AWS --password-stdin "$ECR_REGISTRY"
                    '''
                }
            }
        }

        stage('Tag & Push Images') {
            when {
                branch 'main'
            }
            steps {
                sh '''
                    # Backend
                    docker tag smart_travel_planner-backend:latest "$BACKEND_IMAGE:$IMAGE_TAG"
                    docker tag smart_travel_planner-backend:latest "$BACKEND_IMAGE:latest"
                    docker push "$BACKEND_IMAGE:$IMAGE_TAG"
                    docker push "$BACKEND_IMAGE:latest"

                    # Frontend (built with same-origin VITE_API_URL for in-cluster routing)
                    docker tag smart_travel_planner-frontend:latest "$FRONTEND_IMAGE:$IMAGE_TAG"
                    docker tag smart_travel_planner-frontend:latest "$FRONTEND_IMAGE:latest"
                    docker push "$FRONTEND_IMAGE:$IMAGE_TAG"
                    docker push "$FRONTEND_IMAGE:latest"
                '''
            }
        }

        stage('Provision Infrastructure (Terraform)') {
            when {
                allOf {
                    branch 'main'
                    expression { params.RUN_TERRAFORM == true }
                }
            }
            steps {
                withCredentials([[
                    $class: 'AmazonWebServicesCredentialsBinding',
                    credentialsId: 'aws-jenkins-deploy'
                ]]) {
                    sh '''
                        cd infra/terraform
                        terraform init -input=false
                        terraform plan -out=tfplan -input=false
                        terraform apply -input=false tfplan
                    '''
                }
            }
        }

        stage('Deploy to EKS') {
            when {
                branch 'main'
            }
            steps {
                withCredentials([[
                    $class: 'AmazonWebServicesCredentialsBinding',
                    credentialsId: 'aws-jenkins-deploy'
                ]]) {
                    sh '''
                        aws eks update-kubeconfig --name "$EKS_CLUSTER_NAME" --region "$AWS_REGION"

                        # Point the manifests at the images just pushed
                        sed -i "s#<ECR_BACKEND_REPO_URL>:latest#$BACKEND_IMAGE:$IMAGE_TAG#" infra/k8s/03-backend-deployment.yaml
                        sed -i "s#<ECR_FRONTEND_REPO_URL>:latest#$FRONTEND_IMAGE:$IMAGE_TAG#" infra/k8s/05-frontend-deployment.yaml

                        kubectl apply -f infra/k8s/00-namespace.yaml
                        kubectl apply -f infra/k8s/ -n "$K8S_NAMESPACE"

                        kubectl rollout status deployment/backend -n "$K8S_NAMESPACE" --timeout=120s
                        kubectl rollout status deployment/frontend -n "$K8S_NAMESPACE" --timeout=120s
                    '''
                }
            }
        }
    }

    post {
        success {
            echo "CI/CD pipeline completed successfully — images pushed as tag ${IMAGE_TAG} and deployed to ${EKS_CLUSTER_NAME}."
        }

        failure {
            echo 'CI/CD pipeline failed. Check the logs.'
        }

        always {
            sh 'docker logout "$ECR_REGISTRY" || true'
        }
    }
}