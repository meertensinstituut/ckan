// recline preview module
ckan.module('reclinepreview', function (jQuery, _) {
  return {
    options: {
      i18n: {
        errorLoadingPreview: "Could not load preview",
        errorDataProxy: "DataProxy returned an error",
        errorDataStore: "DataStore returned an error",
        previewNotAvailableForDataType: "Preview not available for data type: "
      }
    },
    initialize: function() {
      this.loadPreviewDialog(preload_resource);
    },
    // **Public: Loads a data preview**
    //
    // Fetches the preview data object from the link provided and loads the
    // parsed data from the webstore displaying it in the most appropriate
    // manner.
    //
    // link - Preview button.
    //
    // Returns nothing.
    loadPreviewDialog: function (resourceData) {
      var self = this;

      function showError(msg){
        msg = msg || _('error loading preview');
        return $('#ckanext-datapreview')
          .append('<div></div>')
          .addClass('alert alert-error fade in')
          .html(msg);
      }

      // 3 situations
      // a) something was posted to the datastore - need to check for this
      // b) csv or xls (but not datastore)
      // c) can be treated as plain text
      resourceData.formatNormalized = this.normalizeFormat(resourceData.format);

      resourceData.url  = this.normalizeUrl(resourceData.url);
      if (resourceData.formatNormalized === '') {
        var tmp = resourceData.url.split('/');
        tmp = tmp[tmp.length - 1];
        tmp = tmp.split('?'); // query strings
        tmp = tmp[0];
        var ext = tmp.split('.');
        if (ext.length > 1) {
          resourceData.formatNormalized = ext[ext.length-1];
        }
      }

      // Set recline CKAN backend API endpoint to right location (so it can locate
      // CKAN DataStore)
      recline.Backend.Ckan.API_ENDPOINT = $('body').data('site-root') + 'api';

      if (resourceData.datastore_active) {
        resourceData.backend =  'ckan';
        var dataset = new recline.Model.Dataset(resourceData);
        var errorMsg = this.options.i18n.errorLoadingPreview + ': ' + this.options.i18n.errorDataStore;
        dataset.fetch()
          .done(function(dataset){
              self.initializeDataExplorer(dataset);
          })
          .fail(function(error){
            if (error.message) errorMsg += ' (' + error.message + ')';
            showError(errorMsg);
          });

      } else if (resourceData.formatNormalized in {'csv': '', 'xls': ''}) {
        // set format as this is used by Recline in setting format for DataProxy
        resourceData.format = resourceData.formatNormalized;
        resourceData.backend = 'dataproxy';
        var dataset = new recline.Model.Dataset(resourceData);
        var errorMsg = this.options.i18n.errorLoadingPreview + ': ' +this.options.i18n.errorDataProxy;
        dataset.fetch()
          .done(function(dataset){

            dataset.bind('query:fail', function(error) {
              $('.data-view-container', self.el).hide();
              $('.header', self.el).hide();
            });

            self.initializeDataExplorer(dataset);
            $('.recline-query-editor .text-query').hide();
          })
          .fail(function(error){
            if (error.message) errorMsg += ' (' + error.message + ')';
            showError(errorMsg);
          });
      } else if (resourceData.formatNormalized in {
        'rdf+xml': '',
        'owl+xml': '',
        'xml': '',
        'n3': '',
        'n-triples': '',
        'turtle': '',
        'plain': '',
        'atom': '',
        'tsv': '',
        'rss': '',
        'txt': ''
        }) {
          // HACK: treat as plain text / csv
          // pass url to jsonpdataproxy so we can load remote data (and tell dataproxy to treat as csv!)
          var _url = this.jsonpdataproxyUrl + '?type=csv&url=' + resourceData.url;
          this.getResourceDataDirect(_url, function(data) {
            this.showPlainTextData(data);
          });
      }
    },
    initializeDataExplorer: function(dataset) {
      var views = [
        {
          id: 'grid',
          label: 'Grid',
          view: new recline.View.SlickGrid({
            model: dataset
          })
        },
        {
          id: 'graph',
          label: 'Graph',
          view: new recline.View.Graph({
            model: dataset
          })
        },
        {
          id: 'map',
          label: 'Map',
          view: new recline.View.Map({
            model: dataset
          })
        }
      ];

      var dataExplorer = new recline.View.MultiView({
        el: this.el,
        model: dataset,
        views: views,
        config: {
          readOnly: true
        }
      });

      // Hide the fields control by default
      // (This should be done in recline!)
      $('.menu-right a[data-action="fields"]').click();
    },
    showError: function (error) {
      var _html = _.template(
          '<div class="alert alert-error"><strong><%= title %></strong><br /><%= message %></div>',
          error
      );
      this.el.html(_html);
    },
    normalizeFormat: function(format) {
      var out = format.toLowerCase();
      out = out.split('/');
      out = out[out.length-1];
      return out;
    },
    normalizeUrl: function(url) {
      if (url.indexOf('https') === 0) {
        return 'http' + url.slice(5);
      } else {
        return url;
      }
    },
    // **Public: Creates a link to the embeddable page.
    //
    // For a given DataExplorer state, this function constructs and returns the
    // url to the embeddable view of the current dataexplorer state.
    makeEmbedLink: function(explorerState) {
      var state = explorerState.toJSON();
      state.state_version = 1;

      var queryString = '?';
      var items = [];
      $.each(state, function(key, value) {
        if (typeof(value) === 'object') {
          value = JSON.stringify(value);
        }
        items.push(key + '=' + escape(value));
      });
      queryString += items.join('&');
      return embedPath + queryString;
    }
  };
});