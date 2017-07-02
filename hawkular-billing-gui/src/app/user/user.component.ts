import { Component, OnInit } from '@angular/core';

import { Tenant } from '../types';
import { DataService } from '../data.service';

@Component({
  selector: 'app-user',
  templateUrl: './user.component.html',
  styleUrls: ['./user.component.css']
})
export class UserComponent implements OnInit {
    tenants: Tenant[];

    constructor(private dataService: DataService) { }

    ngOnInit() {
      this.tenants = this.dataService.getTenants()
    }
}
