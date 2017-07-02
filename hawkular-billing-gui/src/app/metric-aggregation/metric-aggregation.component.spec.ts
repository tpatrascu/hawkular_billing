import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { MetricAggregationComponent } from './metric-aggregation.component';

describe('MetricAggregationComponent', () => {
  let component: MetricAggregationComponent;
  let fixture: ComponentFixture<MetricAggregationComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ MetricAggregationComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MetricAggregationComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should be created', () => {
    expect(component).toBeTruthy();
  });
});
