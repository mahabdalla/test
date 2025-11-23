flectra.define('construction_management.ConstructionDashboard', function (require) {
  'use strict';
  var AbstractAction = require('web.AbstractAction');
  var core = require('web.core');
  var _t = core._t;
  
  var ActionMenu = AbstractAction.extend({
    template: 'constructionDashboard',
    events: {
      'click .total-construction-site': 'view_total_construction_site',
      'click .planning-construction-site': 'planning_construction_site',
      'click .job-order-construction-site': 'view_job_order_construction_site',
      'click .site-in_progress': 'view_site_in_progress',
      'click .complete-site': 'view_complete_site',
    },
    renderElement: function () {
      var self = this;
      this._super.apply(this, arguments);
      this._rpc({
        model: "construction.dashboard",
        method: "get_construction_stats",
      }).then(function (result) {
        self.$('#total_site').empty().append(result['total_site']);
        self.$('#planning_site').empty().append(result['planning_site']);
        self.$('#job_order').empty().append(result['job_order']);
        self.$('#site_in_progress').empty().append(result['site_in_progress']);
        self.$('#complete_site').empty().append(result['complete_site']);
        self.siteState(result['site_state']);
        self.siteType(result['site_type']);
        self.getSiteTimeline(result['construction_time_line']);
        self.getMaterialEquipmentPo(result['material_equipment_po']);
      });
    },
    view_total_construction_site: function (ev) {
      ev.preventDefault();
      ev.stopPropagation();
      return this.do_action({
        name: _t('Total Site'),
        type: 'ir.actions.act_window',
        res_model: 'construction.site',
        views: [[false, 'list'], [false, 'form']],
        target: 'current'
      });
    },
    planning_construction_site: function (ev) {
      ev.preventDefault();
      ev.stopPropagation();
      return this.do_action({
        name: _t('In Planning'),
        type: 'ir.actions.act_window',
        res_model: 'job.costing',
        domain: [['state', '=', 'planning']],
        views: [[false, 'list'], [false, 'form']],
        target: 'current'
      });
    },
    view_job_order_construction_site: function (ev) {
      ev.preventDefault();
      ev.stopPropagation();
      return this.do_action({
        name: _t('Job Order'),
        type: 'ir.actions.act_window',
        res_model: 'construction.details',
        domain: [['stage', '=', 'confirm']],
        views: [[false, 'list'], [false, 'form']],
        target: 'current'
      });
    },
    view_site_in_progress: function (ev) {
      ev.preventDefault();
      ev.stopPropagation();
      return this.do_action({
        name: _t('In Progress'),
        type: 'ir.actions.act_window',
        res_model: 'construction.details',
        domain: [['stage', '=', 'in_progress']],
        views: [[false, 'list'], [false, 'form']],
        target: 'current'
      });
    },
    view_complete_site: function (ev) {
      ev.preventDefault();
      ev.stopPropagation();
      return this.do_action({
        name: _t('Completed Site'),
        type: 'ir.actions.act_window',
        res_model: 'construction.details',
        domain: ['|', ['stage', '=', 'done'], ['stage', '=', 'close']],
        views: [[false, 'list'], [false, 'form']],
        target: 'current'
      });
    },

    get_action: function (ev, name, res_model) {
      ev.preventDefault();
      ev.stopPropagation();
      return this.do_action({
        name: _t(name),
        type: 'ir.actions.act_window',
        res_model: res_model,
        views: [[false, 'kanban'], [false, 'tree'], [false, 'form']],
        target: 'current'
      });
    },
    apexGraph: function () {
      if (typeof Apex !== 'undefined') {
        Apex.grid = {
          padding: {
            right: 0,
            left: 0,
            top: 10,
          }
        };
        Apex.dataLabels = {
          enabled: false
        };
      }
    },
    //    Graph
    siteState: function (data) {
      var options = {
        series: data[1],
        chart: {
          type: 'donut',
          height: 410
        },
        colors: ['#95e2f9', '#f9aa4f', '#efe7ac', '#9daacf', '#62dfc7', '#ff5765'],
        dataLabels: {
          enabled: false
        },
        labels: data['0'],
        legend: {
          position: 'bottom',
        },
      };
      this.renderGraph("#site_state", options);
    },
    siteType: function (data) {
      var options = {
          series: data[1],
          chart: {
           height: 410,
          type: 'polarArea'
        },
        labels: data[0],
        fill: {
          opacity: 1
        },
        stroke: {
          width: 1,
           colors:['#46C2CB', '#54478c', '#0db39e',  '#b9e769',  '#83e377', '#16db93', '#D09CFA', '#048ba8', '#2c699a', '#FFFFD0'],
        },
        yaxis: {
          show: false
        },
        legend: {
          position: 'bottom'
        },
        theme: {
         colors:['#46C2CB', '#54478c', '#0db39e',  '#b9e769',  '#83e377', '#16db93', '#D09CFA', '#048ba8', '#2c699a', '#FFFFD0'],
        }
      };
      this.renderGraph("#site_type", options);
    },
    getMaterialEquipmentPo: function (data) {
      var options = {
        series: [{
          name: "Equipment Purchase Order",
          data: data[1]
        },
        {
          name: "Material Purchase Order",
          data: data[2]
        }
        ],
        chart: {
          height: 350,
          type: 'line',
          zoom: {
            enabled: true
          },
        },
        dataLabels: {
          enabled: false
        },
        legend: {
          tooltipHoverFormatter: function (val, opts) {
            return val + ' - ' + opts.w.globals.series[opts.seriesIndex][opts.dataPointIndex] + ''
          }
        },
        markers: {
          size: 0,
          hover: {
            sizeOffset: 6
          }
        },
        xaxis: {
          categories: data[0],
        },
        tooltip: {
          y: [
            {
              title: {
                formatter: function (val) {
                  return val + " count"
                }
              }
            },
            {
              title: {
                formatter: function (val) {
                  return val + " count"
                }
              }
            },
            {
              title: {
                formatter: function (val) {
                  return val;
                }
              }
            }
          ]
        },
        grid: {
          borderColor: '#f1f1f1',
        }
      };
      this.renderGraph("#equipment_material_po", options);
    },
    getSiteTimeline: function (data) {
      var site_data = [];
      for (var i = 0; i < data.length; i++) {
        var ss = data[i];
        site_data.push({
          'name': ss['name'],
          'data': [{
            'x': 'Site Duration',
            'y': [new Date(ss['start_date']).getTime(), new Date(ss['end_date']).getTime()]
          }]
        });
      }
      var options = {
        series: site_data,
        chart: {
          height: 350,
          type: 'rangeBar'
        },
        plotOptions: {
          bar: {
            horizontal: true
          }
        },
        dataLabels: {
          enabled: true,
          formatter: function (val) {
            if (!val || val.length < 2 || !val[0] || !val[1]) {
              return '0 day';
            }
            var durationMs = val[1] - val[0];
            var days = Math.max(Math.round(durationMs / 86400000), 0);
            return days + (days === 1 ? ' day' : ' days');
          }
        },
        fill: {
          type: 'gradient',
          gradient: {
            shade: 'light',
            type: 'vertical',
            shadeIntensity: 0.25,
            gradientToColors: undefined,
            inverseColors: true,
            opacityFrom: 1,
            opacityTo: 1,
            stops: [50, 0, 100, 100]
          }
        },
        xaxis: {
          type: 'datetime'
        }
      };
      this.renderGraph("#construction_time_line", options);
    },


    renderGraph: function (render_id, options) {
      // Gracefully skip graphs if ApexCharts is not loaded
      if (typeof window !== 'undefined' && typeof window.ApexCharts === 'undefined') {
        return;
      }
      this.$(render_id).empty();
      var graphData = new ApexCharts(document.querySelector(render_id), options);
      graphData.render();
    },
    willStart: function () {
      var self = this;
      self.drpdn_show = false;
      return this._super.apply(this, arguments);
    },
  });
  core.action_registry.add('construction_dashboard', ActionMenu);
});
