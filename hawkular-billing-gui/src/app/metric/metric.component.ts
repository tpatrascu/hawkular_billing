import { Component, Input, OnInit } from '@angular/core';

import { Tenant } from '../types'
import { Metric } from '../types'

@Component({
  selector: 'app-metric',
  templateUrl: './metric.component.html',
  styleUrls: ['./metric.component.css']
})
export class MetricComponent implements OnInit {
    @Input() tenant: Tenant;
    @Input() metric: Metric;
    
    constructor() { }

    ngOnInit() {
    }
}
