describe('Index', function() {
  beforeEach(function() {
      window.swampdragon = {
          onChannelMessage: sinon.spy(),
          ready: sinon.spy()
      };
  });
  beforeEach(module('InstanceApp'));

  var $controller;

  beforeEach(inject(function(_$controller_){
    // The injector unwraps the underscores (_) from around the parameter names when matching
    $controller = _$controller_;
  }));

  describe('$scope.select', function() {
    var $scope, controller;

    beforeEach(function() {
      $scope = {};
      controller = $controller('Index', { $scope: $scope });
    });

    it('selects the instance', function() {
      $scope.select('a', 'b');
      expect($scope.selected.a).toEqual('b');
    });
  });
});
