import { Component, Input, OnInit } from '@angular/core';

import { Tenant } from '../types'


@Component({
  selector: 'app-tenant',
  templateUrl: './tenant.component.html',
  styleUrls: ['./tenant.component.css']
})
export class TenantComponent implements OnInit {
    @Input() tenant: Tenant;

    constructor() { }

    ngOnInit() {
    }

}
