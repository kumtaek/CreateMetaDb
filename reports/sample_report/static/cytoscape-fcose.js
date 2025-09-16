// Stub implementation of cytoscape-fcose layout.
// In offline environments where the official plugin cannot be
// downloaded, this file registers a minimal 'fcose' layout that
// simply delegates to the built-in 'cose' layout. This prevents
// runtime errors and provides a basic force-directed layout.
(function(){
  if (typeof cytoscape === 'undefined') {
    return;
  }

  function FcoseLayout(options){
    this.options = options || {};
    this.cy = this.options.cy;
  }

  FcoseLayout.prototype.run = function(){
    // Fall back to the built-in cose layout
    var opts = Object.assign({}, this.options, { name: 'cose' });
    delete opts.cy;
    this.cy.layout(opts).run();
  };

  FcoseLayout.prototype.stop = function(){
    // no-op
  };

  var register = function(cytoscape){
    cytoscape('layout', 'fcose', FcoseLayout);
  };

  register(cytoscape);
})();