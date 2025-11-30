// firebase-config.js

// 1. Objeto de Configuração
const firebaseConfig = {
    apiKey: "AIzaSyCEW-C1FavyFqjabMjmS-JVo2fLXHNt5Yg",
    authDomain: "meuaplicativosaude.firebaseapp.com",
    projectId: "meuaplicativosaude",
    storageBucket: "meuaplicativosaude.firebasestorage.app",
    messagingSenderId: "547845597696",
    appId: "1:547845597696:web:7942056f2d48601fa086e5",
    measurementId: "G-MYE47X3LNH"
};

// Sobrescreve o appId conforme solicitado
firebaseConfig.appId = "meuappsaude"; 

// 2. INICIALIZAÇÃO DO FIREBASE E SERVIÇOS
// Importante: As variáveis 'app', 'db' e 'auth' SÃO DEFINIDAS AQUI.
// Elas se tornam globais, permitindo o uso em admin-panel.js.

const app = firebase.initializeApp(firebaseConfig);
const db = app.firestore(); // ESTA LINHA É A CHAVE
const auth = app.auth();    // Opcional para o painel, mas bom ter.

// Você pode remover qualquer linha extra que tente redefinir o db aqui.