pipeline {
    agent any
            tools {
                jdk "openjdk15"
            }
            stages {
            stage('Checkout') {
                steps {
                    checkout changelog: true, poll: true, scm: [$class           : 'GitSCM', branches: [[name: '*/master']],
                                                                extensions       : scm.extensions,
                                                                userRemoteConfigs: [[
                                                                                            url          : 'https://github.com/FedorSergeev/leaders2021.git',
                                                                                            credentialsId: 'githubd'
                                                                                    ]]
                    ]
                }
            }
            stage('Build Docker image') {
                            steps {
                                script {
                                    sh '''
                                        cd server_api
                                        docker build -t docker:5000/zusemima/social-predictor:0.1 .
                                    '''
                                }
                            }
            }
            stage('Push Docker image') {
                steps {
                    script {
                        sh 'docker push  docker:5000/zusemima/social-predictor:0.1'
                    }
                }

            }

        }
}