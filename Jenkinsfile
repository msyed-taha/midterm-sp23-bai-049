pipeline {
    agent any

    triggers {
        githubPush()
    }

    options {
        disableConcurrentBuilds()
        timeout(time: 10, unit: 'MINUTES')
        timestamps()
    }

    environment {
        STUDENT_ID = 'SP23-BAI-049'
        IMAGE = 'msyedtaha/midterm-sp23-bai-049'
        CONTAINER = 'midterm-api'
        METRICS_URL = 'http://13.233.51.253:8000/metrics'
        SENDER = 'johnndoeehere@gmail.com'
    }

    stages {
        stage('Fetch latest data') {
            steps {
                script {
                    env.COMMIT_SHA = sh(script: 'git rev-parse HEAD', returnStdout: true).trim()
                }
                sh 'git log -1 --format="Commit %H by %an: %s"'
                sh 'echo "Training rows in dataset/train.csv: $(( $(wc -l < dataset/train.csv) - 1 ))"'
            }
        }

        stage('Prepare CI environment') {
            steps {
                script {
                    docker.build("${IMAGE}:ci", '--target ci .')
                }
            }
        }

        stage('Retrain model') {
            steps {
                script {
                    docker.image("${IMAGE}:ci").inside {
                        sh "rm -rf artifacts && GIT_COMMIT=${env.COMMIT_SHA} python train.py"
                    }
                }
            }
        }

        stage('Test') {
            steps {
                script {
                    docker.image("${IMAGE}:ci").inside {
                        sh "GIT_COMMIT=${env.COMMIT_SHA} python -m pytest -q -p no:cacheprovider"
                    }
                }
            }
        }

        stage('Build Docker image') {
            steps {
                script {
                    docker.build("${IMAGE}:${env.BUILD_NUMBER}", '--target runtime .')
                }
            }
        }

        stage('Deploy on EC2') {
            steps {
                sh '''
                    docker rm -f "$CONTAINER" 2>/dev/null || true
                    docker run -d --name "$CONTAINER" --restart unless-stopped \
                      -p 8000:8000 "$IMAGE:$BUILD_NUMBER"

                    # Wait until the live API reports the model trained from this commit.
                    for attempt in $(seq 1 30); do
                      if curl -fs http://127.0.0.1:8000/metrics | grep -q "$COMMIT_SHA"; then
                        curl -s http://127.0.0.1:8000/metrics
                        exit 0
                      fi
                      sleep 2
                    done
                    docker logs "$CONTAINER"
                    exit 1
                '''
            }
        }

        stage('Push to Docker Hub') {
            steps {
                script {
                    docker.withRegistry('https://index.docker.io/v1/', 'dockerhub-creds') {
                        def image = docker.image("${IMAGE}:${env.BUILD_NUMBER}")
                        image.push()
                        image.push('latest')
                    }
                }
            }
        }
    }

    post {
        always {
            script {
                def result = currentBuild.currentResult
                def metrics = sh(script: 'cat artifacts/metrics.json 2>/dev/null || echo "not available"', returnStdout: true).trim()
                def cause = currentBuild.getBuildCauses().collect { it.shortDescription }.join(', ')
                def summary = result == 'SUCCESS' ?
                    'New training data was received from GitHub. The model was retrained, tested, packaged as a Docker image and redeployed on AWS EC2.' :
                    'The pipeline did not complete. The previously deployed model is still being served.'
                emailext(
                    from: env.SENDER,
                    to: env.NOTIFY_TO ?: 'qasimalik@gmail.com',
                    subject: "[${env.STUDENT_ID}] ${env.JOB_NAME} #${env.BUILD_NUMBER}: ${result} - ML model retraining pipeline",
                    body: """Student Reg No: ${env.STUDENT_ID}
Job: ${env.JOB_NAME} #${env.BUILD_NUMBER}
Result: ${result}
Trigger: ${cause}
Commit: ${env.COMMIT_SHA}

${summary}

Model metrics:
${metrics}

Live endpoint: ${env.METRICS_URL}
Docker image: ${env.IMAGE}:${env.BUILD_NUMBER}
Build log: ${env.BUILD_URL}console
"""
                )
            }
        }
    }
}
