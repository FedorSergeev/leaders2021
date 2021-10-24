pipeline {
    agent any
    stages {
        stage("Deploy Zusemima") {
            steps {
                ansiblePlaybook playbook: 'k8s/deploy-zusemima.yml'
            }
        }
    }
}