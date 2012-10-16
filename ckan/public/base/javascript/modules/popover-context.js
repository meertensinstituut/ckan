/* Popover context
 * These appear when someone hovers over a context item in a activity stream to
 * give the user more context into that particular item. It also allows for people to
 * follow and unfollow quickly from within the popover
 *
 * id - The user_id of user
 * context - The type of this popover: currently supports user & package

 * url - The URL of the profile for that user
 * loading - Loading state helper
 * authed - Is the current user authed ... if so what's their user_id
 * template - Simple string-replace template for content of popover
 *
 * Examples
 *
 *   <a data-module="popover-context" data-module-context="user" data-module-id="{user_id}">A user</a>
 *
 */

// Global dictionary and render store for items
window.popover_context = {
	dict: {
		user: {},
		dataset: {}
	},
	render: {
		user: {},
		dataset: {}
	}
};

this.ckan.module('popover-context', function($, _) {
	return {

		/* options object can be extended using data-module-* attributes */
		options : {
			id: null,
			loading: false,
			authed: false,
			url: '',
			i18n: {
				loading: _('Loading...')
			}
		},

		/* Initialises the module setting up elements and event listeners.
		 *
		 * Returns nothing.
		 */
		initialize: function () {
			if (
				this.options.id != true
				&& this.options.id != null
			) {
				$.proxyAll(this, /_on/);
				if ($('.account').hasClass('authed')) {
					this.options.authed = $('.account').data('me');
				}
				this.el.popover({
					animation: false,
					content: this.i18n('loading'),
					placement: 'bottom'
				});
				this.el.on('mouseover', this._onMouseOver);
				this.sandbox.subscribe('follow-follow-' + this.options.id, this._onHandleFollow);
				this.sandbox.subscribe('follow-unfollow-' + this.options.id, this._onHandleFollow);
			}
		},

		loadingHelper: function(loading) {
			this.options.loading = loading;
			var popover = this.el.data('popover');
			if (typeof popover.$tip != 'undefined') {
				var tip = popover.$tip;
				if (loading) {
					tip.addClass('popover-context-loading');
					this.el.popover({
						content: this.i18n('loading')
					});
				} else {
					tip.removeClass('popover-context-loading');
				}
			}
		},

		/* Handles the showing of the popover on hover (also hides other active popovers)
		 *
		 * Returns nothing.
		 */
		_onMouseOver: function() {
			$('[data-module="popover-context"]').popover('hide');
			this.el.popover('show');
			this.getData();
		},

		/* Get's the data from the ckan api
		 *
		 * Returns nothing.
		 */
		getData: function() {
			if (!this.options.loading) {
				this.loadingHelper(true);
				var id = this.options.id;
				var type = this.options.type;
				if (typeof window.popover_context.dict[type][id] == 'undefined') {
					var client = this.sandbox.client;
					var endpoint = ( type == 'user' ) ? 'user_show' : 'package_show';
					this.loadingHelper(true);
					client.call('GET', endpoint, '?id=' + id, this._onHandleData);
				} else {
					this._onHandleData(window.popover_context.dict[type][id]);
				}
			}
		},

		/* Callback from getting the endpoint from the ckan api
		 *
		 * Returns nothing.
		 */
		_onHandleData: function(json) {
			if (json.success) {
				var id = this.options.id;
				var type = this.options.type;
				var client = this.sandbox.client;
				// set the dictionary
				window.popover_context.dict[type][id] = json;

				// has this been rendered before?
				if (typeof window.popover_context.render[type][id] == 'undefined') {
					var params = this.sanitiseParams(json.result);
					client.getTemplate('popover-context-' + type + '.html', params, this._onRenderPopover);
				} else {
					this._onRenderPopover(window.popover_context.render[type][id]);
				}
			}
		},

		/* Used to break down a raw object into something a little more passable into a GET request
		 *
		 * Returns object.
		 */
		sanitiseParams: function(raw) {
			var type = this.options.type;
			var params = {};
			if (type == 'user') {
				params.id = raw.id;
				params.title = raw.name;
				params.about = raw.about;
				params.display_name = raw.display_name;
				params.num_followers = raw.num_followers;
				params.number_administered_packages = raw.number_administered_packages;
				params.number_of_edits = raw.number_of_edits;
				params.is_me = ( raw.id == this.options.authed );
			} else if (type == 'dataset') {
				params.id = raw.id;
				params.title = raw.title;
				params.name = raw.name;
				params.notes = raw.notes;
				params.num_resources = raw.resources.length;
				params.num_tags = raw.tags.length;
			}
			return params;
		},

		/* Renders the contents of the popover
		 *
		 * Returns nothing.
		 */
		_onRenderPopover: function(html) {
			var id = this.options.id;
			var type = this.options.type;
			var dict = window.popover_context.dict[type][id].result;
			var popover = this.el.data('popover');
			if (typeof popover.$tip != 'undefined') {
				var tip	= popover.$tip;
				var title = ( type == 'user' ) ? dict.display_name : dict.title;
				$('.popover-title', tip).html('<a href="javascript:;" class="popover-close">&times;</a>' + title);
				$('.popover-content', tip).html(html);
				$('.popover-close', tip).on('click', this._onClickPopoverClose);
				var follow_check = this.getFollowButton();
				if (follow_check) {
					ckan.module.initializeElement(follow_check[0]);
				}
				this.loadingHelper(false);
			}
			// set the global
			window.popover_context.render[type][id] = html;
		},

		/* Handles closing the currently open popover
		 *
		 * Returns nothing.
		 */
		_onClickPopoverClose: function() {
			this.el.popover('hide');
		},

		/* Handles getting the follow button form within a popover
		 *
		 * Returns jQuery collection || false.
		 */
		getFollowButton: function() {
			var popover = this.el.data('popover');
			if (typeof popover.$tip != 'undefined') {
				var button = $('[data-module="follow"]', popover.$tip);
				if (check.length > 0) {
					return button;
				}
			}
			return false;
		},

		/* Callback from when you follow/unfollopw a specified item... this is used to ensure
		 * all popovers associated to that user get re-populated
		 *
		 * Returns nothing.
		 */
		_onHandleFollow: function() {
			var client = this.sandbox.client;
			var button = this.getFollowButton();
			if (button) {
				client.getTemplate('follow_button.html', { type: this.options.type, id: this.options.id }, this._onHandleFollowData);
			}
		},

		_onHandleFollowData: function(html) {
			var button = this.getFollowButton();
			if (button) {
				$(html).insertAfter(button);
				button.remove();
				var new_button = this.getFollowButton();
				ckan.module.initializeElement(new_button[0]);
			}
		}

	};
});
