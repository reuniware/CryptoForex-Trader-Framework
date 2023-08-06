// Création du module principal de l'application
angular.module('myApp', []);

// Définition du contrôleur MainController
angular.module('myApp').controller('MainController', function($scope) {
  $scope.assets = [];
  $scope.filterText = ''; // Variable pour le filtrage

  // URL du websocket Binance pour les cours de tous les actifs
  var wsUrl = 'wss://stream.binance.com:9443/ws/!ticker@arr';

  // Création d'une instance de websocket
  var ws = new WebSocket(wsUrl);

  // Événement lorsque la connexion websocket est ouverte
  ws.onopen = function() {
    console.log('Connexion websocket établie');
  };

  // Événement lorsque des données sont reçues depuis le serveur
  ws.onmessage = function(event) {
    // La donnée reçue est au format JSON
    var data = JSON.parse(event.data);
    $scope.assets = data; // Mettre à jour la liste des actifs
    $scope.$apply(); // Mettre à jour la vue AngularJS
  };

  // Événement en cas d'erreur de la connexion websocket
  ws.onerror = function(event) {
    console.error('Erreur WebSocket :', event);
  };

  // Fonction pour trier les actifs par ordre alphabétique
  function sortAssets() {
    $scope.sortedAssets = $scope.assets.sort(function(a, b) {
      var symbolA = a.s.toUpperCase();
      var symbolB = b.s.toUpperCase();
      if (symbolA < symbolB) return -1;
      if (symbolA > symbolB) return 1;
      return 0;
    });
  }

  // Appel initial pour trier les actifs
  sortAssets();

  // Fonction pour calculer le pourcentage d'évolution
  $scope.getPercentageChange = function(currentPrice, openPrice) {
    var change = currentPrice - openPrice;
    return ((change / openPrice) * 100).toFixed(2) + '%';
  };

  // Actualiser les cours de tous les actifs toutes les secondes (1000 millisecondes)
  setInterval(function() {
    sortAssets();
    $scope.$apply(); // Mettre à jour la vue AngularJS
  }, 1000);
});
