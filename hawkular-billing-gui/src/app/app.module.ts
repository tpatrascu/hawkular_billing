import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';

import { RouterModule } from '@angular/router';

import { AppComponent } from './app.component';
import { UserComponent } from './user/user.component';
import { TenantComponent } from './tenant/tenant.component';
import { MetricComponent } from './metric/metric.component';
import { MetricDataComponent } from './metric-data/metric-data.component';
import { MetricAggregationComponent } from './metric-aggregation/metric-aggregation.component';

import { Tenant } from './types';
import { DataService } from './data.service';

@NgModule({
  declarations: [
    AppComponent,
    UserComponent,
    TenantComponent,
    MetricComponent,
    MetricDataComponent,
    MetricAggregationComponent
  ],
  imports: [
    BrowserModule,
    RouterModule.forRoot([
        {
            path: 'user',
            component: UserComponent
        },
        {
            path: 'tenant',
            component: TenantComponent
        },
        {
            path: '',
            redirectTo: '/user',
            pathMatch: 'full'
        },
    ])
  ],
  providers: [DataService],
  bootstrap: [AppComponent]
})
export class AppModule { }
